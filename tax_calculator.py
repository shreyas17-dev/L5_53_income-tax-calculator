"""Personal income-tax calculator with PAN, Form 16 and CGI helpers."""
import os
import re
from wsgiref.handlers import CGIHandler  # nosec B412

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from defusedxml import minidom

# Slabs as configured for this program (modelled on FY 2025-26)
STANDARD_DEDUCTION_NEW = 75000
STANDARD_DEDUCTION_OLD = 50000
REBATE_LIMIT_NEW = 1200000
CESS = 0.04
PAN_KEY = (
    bytes.fromhex(os.environ["PAN_KEY_HEX"])
    if "PAN_KEY_HEX" in os.environ
    else AESGCM.generate_key(bit_length=256)
)
NEW_SLABS = [(400000, 0.0), (800000, 0.05), (1200000, 0.10),
             (1600000, 0.15), (2000000, 0.20), (2400000, 0.25),
             (float("inf"), 0.30)]
OLD_SLABS = [(250000, 0.0), (500000, 0.05), (1000000, 0.20),
             (float("inf"), 0.30)]


def slab_tax(taxable, slabs, lower=0):
    """Return tax before cess, applying each slab rate only to its band."""
    tax = 0
    for limit, rate in slabs:
        if taxable > lower and limit > lower:
            tax += (min(taxable, limit) - lower) * rate
        lower = max(lower, limit)
    return tax


def new_regime_tax(salary):
    """Tax under the new regime, including cess."""
    taxable = salary - STANDARD_DEDUCTION_NEW
    tax_amount = slab_tax(taxable, NEW_SLABS)
    if taxable <= REBATE_LIMIT_NEW:
        tax_amount = 0
    return int(tax_amount * (1 + CESS))


def basic_exemption(age):
    """Return the basic exemption limit for the given age."""
    if 60 <= age < 80:
        return 300000
    if age >= 80:
        return 500000
    return 250000


def old_regime_tax(salary, age, deductions):
    """Tax under the old regime, including cess."""
    taxable = salary - STANDARD_DEDUCTION_OLD - sum(deductions.values())
    tax_amount = slab_tax(taxable, OLD_SLABS, basic_exemption(age))
    return int(tax_amount * (1 + CESS))


def better_regime(salary, age, deductions):
    """Return the regime ("new" or "old") with the lower tax."""
    new_tax = new_regime_tax(salary)
    old_tax = old_regime_tax(salary, age, deductions)
    return "new" if new_tax < old_tax else "old"


def is_valid_pan(pan):
    """Return True if pan matches the format AAAAA9999A."""
    try:
        return bool(re.fullmatch(r"[A-Z]{5}[0-9]{4}[A-Z]", pan))
    except TypeError:
        return False


def encrypt_pan(pan):
    """Encrypt a PAN with AES-GCM and return nonce + ciphertext as hex."""
    nonce = os.urandom(12)
    return (nonce + AESGCM(PAN_KEY).encrypt(nonce, pan.encode(), None)).hex()


def signing_key():
    """Generate an RSA private key for signing."""
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def parse_form16(xml_text):
    """Return (salary, tds) read from a Form 16 XML string."""
    doc = minidom.parseString(xml_text)
    salary_text = doc.getElementsByTagName("salary")[0].firstChild.data
    tds_text = doc.getElementsByTagName("tds")[0].firstChild.data
    return int(salary_text), int(tds_text)


def run_as_cgi(app):
    """Run a WSGI app as a CGI script."""
    os.environ.pop("HTTP_PROXY", None)  # mitigate httpoxy
    CGIHandler().run(app)  # nosec B412


def main():
    """Print sample calculations."""
    print("New regime, salary 12,75,000:", new_regime_tax(1275000))
    print("New regime, salary 18,00,000:", new_regime_tax(1800000))
    deductions = {"80C": 200000, "80D": 30000}
    print("Old regime, salary 18,00,000:",
          old_regime_tax(1800000, 35, deductions))
    print(f"Better regime: {better_regime(1800000, 35, deductions)}")
    print(f"Basic exemption at age 80: {basic_exemption(80)}")
    print("PAN 'ABCDE1234FXYZ' valid?", is_valid_pan("ABCDE1234FXYZ"))
    same = encrypt_pan("ABCDE1234F") == encrypt_pan("ABCDE1234F")
    print("Same PAN encrypts the same way twice?", same)
    form16 = ("<form16><salary>1800000</salary>"
              "<tds>150000</tds></form16>")
    print("Form 16:", parse_form16(form16))
    print(f"Signing key size: {signing_key().key_size}")


if __name__ == "__main__":
    main()
