import os
from pathlib import Path


# Load seed phrase from .env.secrets (not hardcoded)
def load_seed_phrase():

    secrets_path = Path(
        os.environ.get("AIG_SECRETS_PATH", os.path.expanduser("~/Documents/XXX/anty/.env.secrets"))
    )
    if not secrets_path.exists():
        raise FileNotFoundError(f"Secrets file not found: {secrets_path}")
    for line in secrets_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("SAFEPAL_SEED_PHRASE="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise ValueError("SAFEPAL_SEED_PHRASE not found in .env.secrets")


try:
    from eth_account import Account
    from eth_account.hdaccount import HDPath, seed_from_mnemonic

    seed_phrase = load_seed_phrase()

    # Derivar semilla BIP39
    seed = seed_from_mnemonic(seed_phrase, "")

    # Derivar clave privada usando HDPath (BIP44 para Ethereum)
    # Path: m/44'/60'/0'/0/0
    hd_path = HDPath("m/44'/60'/0'/0/0")
    private_key = hd_path.derive(seed)

    # Crear cuenta
    account = Account.from_key(private_key)

    print("=" * 60)
    print("SAFEPAL WALLET - DERIVACION DESDE .env.secrets")
    print("=" * 60)
    print(f"DIRECCION ETHEREUM: {account.address}")
    print("=" * 60)
    print("Seed phrase loaded from .env.secrets (not displayed)")
    print("Private key derived (not displayed)")
except ImportError:
    print("eth_account not installed. Run: pip install eth-account")
except Exception as e:
    print(f"Error: {e}")
