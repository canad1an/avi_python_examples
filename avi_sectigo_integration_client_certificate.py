'''
This is to be used as a certificate management profile in Avi Networks. This will integrate with the public CA Sectigo.
This is the client certificate version.
Parameters -
    user                - Sectigo user name.
    orgid               - Secitgo org id.
    customeruri         - Secitogo customer URI.
    certtype            - Certificate type. Default type 3.
    term                - Certificate term. Default 365.
    comments            - Comments for order.
'''

import json, time, requests, os
from tempfile import NamedTemporaryFile

def get_crt(csr, user, orgid, certtype, term, comments, customeruri, client_crt, client_key):

    def _generate_certificate(csr, user, orgid, certtype, term, comments, customeruri, client_crt, client_key):
        payload = {
            "orgId": orgid,
            "csr": csr,
            "certType": certtype,
            "term": term,
            "comments": comments
            }
        headers = {
            "login": user,
            "customerUri": customeruri
            }
        print ("Generating certificate...")
        r = requests.post ("https://cert-manager.com/private/api/ssl/v1/enroll/", json=payload, headers=headers, cert=(client_crt, client_key))
        if r.status_code >= 300:
            err_msg = "Failed to generate certificate. Response status - {}, text - {}".format(r.status_code, r.text)
            raise Exception(err_msg)
        print ("Certificate Generated..." + r.text)
        return json.loads(r.text)

    def _get_certificate(user, customeruri, sslid, formattype, client_crt, client_key):
        headers = {
            "login": user,
            "customerUri": customeruri
            }
        print ("Downloading certificate...")
        r = requests.get ("https://cert-manager.com/private/api/ssl/v1/collect/" + str(sslid) + "/" + formattype, headers=headers, cert=(client_crt, client_key))
        if r.status_code >= 300:
            err_msg = "Failed to download certificate. Response status - {}, text - {}".format(r.status_code, r.text)
            raise Exception(err_msg)
        print ("Certificate downloaded..." + r.text)
        return r.text

    crt_id = _generate_certificate(csr, user, orgid, certtype, term, comments, customeruri, client_crt, client_key)
    time.sleep(20)
    cert = _get_certificate(user, customeruri, crt_id["sslId"], "x509CO", client_crt, client_key)
    return cert

def certificate_request(csr, common_name, kwargs):
    user = kwargs.get("user", None)
    customeruri = kwargs.get("customeruri", None)
    orgid = kwargs.get("orgid", None)
    certtype = kwargs.get("certtype", "3")
    term = kwargs.get("term", "365")
    comments = kwargs.get("comments", "")

    if not user:
        raise Exception("Missing user argument.")
    if not orgid:
        raise Exception("Missing orgid argument.")
    if not customeruri:
        raise Exception("Missing customeruri argument.")

    client_key = '''-----BEGIN RSA PRIVATE KEY-----

-----END RSA PRIVATE KEY-----'''

    client_crt = '''-----BEGIN CERTIFICATE-----

-----END CERTIFICATE-----'''

    crt_temp_file = NamedTemporaryFile(mode='w',delete=False)
    crt_temp_file.close()
    with open(crt_temp_file.name, 'w') as f:
        f.write(client_crt)

    key_temp_file = NamedTemporaryFile(mode='w',delete=False)
    key_temp_file.close()
    with open(key_temp_file.name, 'w') as f:
        f.write(client_key)

    signed_crt = None
    try:
        signed_crt = get_crt(csr, user, orgid, certtype, term, comments, customeruri, crt_temp_file.name, key_temp_file.name)
    finally:
        os.remove(crt_temp_file.name)
        os.remove(key_temp_file.name)

    return signed_crt