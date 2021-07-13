'''
Parameters -
    user                - Sectigo user name.
    orgid               - Secitgo org id.
    customeruri         - Secitogo customer URI.
    certtype            - Optional - Certificate type. Default type 3.
    term                - Optional - Certificate term. Default 365.
    comments            - Comments for order.
    wait_timer          - Optional - Wait time between queries to get the generated certificate. Default to 15s
    client_certificate  - The client certificate exactly as it appears. Do not modify formatting
    client_key          - The client key exactly as it appears. Do not modify formatting
'''

import json, time, requests, os, re, logging, os, sys, subprocess
from tempfile import NamedTemporaryFile
from avi.infrastructure.avi_logging import get_root_logger

log = get_root_logger(__name__, '/opt/avi/log/sectigo.log', logging.DEBUG)


def get_crt(csr, user, orgid, certtype, term, comments, customeruri, csrfile, client_crt, client_key, wait_timer):

    # helper function - run external commands
    def _cmd(cmd_list, stdin=None, cmd_input=None, err_msg="Command Line Error"):
        proc = subprocess.Popen(cmd_list, stdin=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate(cmd_input)
        if proc.returncode != 0:
            raise IOError("{0}\n{1}".format(err_msg, err))
        return out

    def _generate_certificate(csr, user, orgid, certtype, term, comments, customeruri, sannames, client_crt, client_key):
        payload = {
            "orgId": orgid,
            "subjAltNames": sannames,
            "csr": csr,
            "certType": certtype,
            "term": term,
            "comments": comments
            }
        headers = {
            "login": user,
            "customerUri": customeruri
            }
        log.info("Generating certificate...!")
        r = requests.post ("https://cert-manager.com/private/api/ssl/v1/enroll/", json=payload, headers=headers, cert=(client_crt, client_key))
        if r.status_code >= 300:
            err_msg = "Failed to generate certificate. Response status - {}, text - {}".format(r.status_code, r.text)
            raise Exception(err_msg)
        log.info("Certificate Generated..." + r.text)
        return json.loads(r.text)

    def _get_certificate(user, customeruri, sslid, formattype, client_crt, client_key):
        headers = {
            "login": user,
            "customerUri": customeruri
            }
        log.info("Downloading certificate")
        r = requests.get ("https://cert-manager.com/private/api/ssl/v1/collect/" + str(sslid) + "/" + formattype, headers=headers, cert=(client_crt, client_key))
        if r.status_code >= 300:
            err_msg = "Failed to download certificate. Response status - {}, text - {}".format(r.status_code, r.text)
            raise Exception(err_msg)
        log.info("Certificate downloaded..." + r.text)
        return r.text

    # find domains
    log.info("Parsing CSR...")
    out = _cmd(["openssl", "req", "-in", csrfile, "-noout", "-text"], err_msg="Error loading {0}".format(csrfile))
    domains = set([])
    common_name = re.search(r"Subject:.*? CN\s?=\s?([^\s,;/]+)", out.decode('utf8'))
    if common_name:
        domains.add(common_name.group(1))
    subject_alt_names = re.search(r"X509v3 Subject Alternative Name: (?:critical)?\n +([^\n]+)\n", out.decode('utf8'), re.MULTILINE|re.DOTALL)
    if subject_alt_names:
        for san in subject_alt_names.group(1).split(", "):
            if san.startswith("DNS:"):
                domains.add(san[4:])
    domains = ",".join(domains)
    log.info("Found domains: {0}".format(domains))

    crt_id = _generate_certificate(csr, user, orgid, certtype, term, comments, customeruri, domains, client_crt, client_key)

    cert = None
    while cert is None:
        log.info("Certificate not available for download yet.. retrying..")
        time.sleep(int(wait_timer))
        cert = _get_certificate(user, customeruri, crt_id["sslId"], "x509CO", client_crt, client_key)
    return cert

def certificate_request(csr, common_name, kwargs):
    user = kwargs.get("user", None)
    customeruri = kwargs.get("customeruri", None)
    orgid = kwargs.get("orgid", None)
    certtype = kwargs.get("certtype", "3")
    term = kwargs.get("term", "365")
    comments = kwargs.get("comments", "")
    wait_timer = kwargs.get("wait_timer", 15)
    client_certificate = kwargs.get("client_certificate", None)
    client_key = kwargs.get("client_key", None)

    if not user:
        raise Exception("Missing user argument.")
    if not orgid:
        raise Exception("Missing orgid argument.")
    if not customeruri:
        raise Exception("Missing customeruri argument.")
    if not client_certificate:
        raise Exception("Missing client_certificate argument.")
    if not client_key:
        raise Exception("Missing client_key argument.")
    
    client_key = client_key[31:-29]
    client_key = client_key.replace(' ', '\n')
    client_key = "-----BEGIN RSA PRIVATE KEY-----" +  client_key + "-----END RSA PRIVATE KEY-----\n"
    client_crt = client_certificate[27:-25]
    client_crt = client_crt.replace(' ', '\n') 
    client_crt = "-----BEGIN CERTIFICATE-----" +  client_crt + "-----END CERTIFICATE-----\n"

    crt_temp_file = NamedTemporaryFile(mode='w',delete=False)
    crt_temp_file.close()
    with open(crt_temp_file.name, 'w') as f:
        f.write(client_crt)

    key_temp_file = NamedTemporaryFile(mode='w',delete=False)
    key_temp_file.close()
    with open(key_temp_file.name, 'w') as f:
        f.write(client_key)

    csr_temp_file = NamedTemporaryFile(mode='w',delete=False)
    csr_temp_file.close()
    with open(csr_temp_file.name, 'w') as f:
        f.write(csr)

    signed_crt = None
    try:
        signed_crt = get_crt(csr, user, orgid, certtype, term, comments, customeruri, csr_temp_file.name, crt_temp_file.name, key_temp_file.name, wait_timer)
    except Exception as e:
        log.info(e)
    finally:
        os.remove(csr_temp_file.name)
        os.remove(crt_temp_file.name)
        os.remove(key_temp_file.name)

    log.info("Certificate generated successfully.")

    return signed_crt
