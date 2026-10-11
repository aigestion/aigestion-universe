"""
SafePal Zendesk Ticket Helper
Opens the Zendesk form and prepares content for pasting.
"""

import webbrowser
import pyperclip

# Zendesk URL
ZENDESK_URL = "https://safepalsupport.zendesk.com/hc/en-us/requests/new?ticket_form_id=360001760732"

# Ticket content
TICKET_SUBJECT = "URGENT — Unauthorized drain from SafePal S1 wallet, PIN never entered, seed compromised + Police Report"

TICKET_BODY = """Hi SafePal Support Team,

I am reporting an urgent security incident: unauthorized transactions drained my SafePal hardware wallet. I never entered my PIN / 6-digit authorization code for these transactions, and I never knowingly shared my 12/24-word seed phrase.

=== 1. MY DETAILS ===
- Name: Alejandro
- Contact email: noemisanalex@hotmail.com
- Device: SafePal Hardware Wallet S1 (protected with PIN/password, physical confirmation always required)
- My wallet address: 0x80e87Dd67d25a2Bb3FCb7b1b84c7a9aBbd1e9b65
- Network: Ethereum mainnet (same seed also used on BSC / Base / Polygon via SafePal App)
- Date of incident: 2026-10-08 (22:44 UTC) to 2026-10-09 (04:59 UTC)
- Estimated total loss reported: ~$6,500 (multi-chain)
- Police report reference/expediente: ES_EA0019657_2026_EXP_AC2000001103104
- Police report CSV: GEISER-b2f5-c990-0231-489f-9481-26bc-01c9-9f19
- Police report registry number: REGAGE26e00088252598
- Filed: 2026-10-10 15:57 via Guardia Civil electronic headquarters

=== 2. ROOT CAUSE FOUND ON-CHAIN ===
On 2026-05-30 at 16:20 UTC I signed an Approve to contract 0xC727f87871ee12Bbcedd2973746D1Deb7529aaD6, labeled on Etherscan as "Fake_Phishing4733383".
Transaction: 0xd0a2c6b431aaf4a8802be43277db766d905a186e6ae14b7be73ffdee997b7df8

=== 3. UNAUTHORIZED DRAIN TRANSACTIONS ===
a) 0xdefb2bd693ccc0cfa7cce6d333cced2c40f12645b5021569cd167cc1abccc9fe
   2026-10-08 22:44 UTC — 0.049199858 ETH to 0xdd90000891a37165ad1Dd6cDb2d77256355AF056

b) 0x148fd00e42875617706abe5575f77e0c358b6aa44eede2d4a14485ee07686661
   2026-10-08 22:45 UTC — 54.89 SFP toward 0xdd90000891a37165ad1Dd6cDb2d77256355AF056

c) 0x903de0a655d4d45219406d36dace8b8f3020174f34651cc5cfbaa027f58f9a70
   2026-10-09 04:07 UTC — Sandbox LAND NFT (Token ID 93495) to 0x9098632319C07c8200e6B9123dd277D70AeC3333

=== 4. ATTACKER ADDRESSES ===
- 0xdd90000891a37165ad1Dd6cDb2d77256355AF056 (main)
- 0x9098632319C07c8200e6B9123dd277D70AeC3333 (NFT receiver)

=== 5. WHAT I ASK FROM SAFEPAL ===
1. Confirm whether the phishing contract 0xC727f87871ee12Bbcedd2973746D1Deb7529aaD6 is a known threat
2. Advise how to verify my SafePal App is genuine and which firmware version is safe
3. Log the attacker addresses in your internal risk/blocklist systems
4. Advise if there are any remaining smart-contract allowances I should revoke
5. Confirm the correct procedure to migrate to a new seed safely

Best regards,
Alejandro
noemisanalex@hotmail.com

Police report: ES_EA0019657_2026_EXP_AC2000001103104 (Guardia Civil, Spain)"""

def main():
    print("=== SafePal Zendesk Ticket Helper ===\n")
    
    # Copy ticket body to clipboard
    print("Copying ticket body to clipboard...")
    pyperclip.copy(TICKET_BODY)
    print("Ticket body copied! (Ctrl+V to paste)\n")
    
    # Open Zendesk in browser
    print(f"Opening Zendesk: {ZENDESK_URL}")
    webbrowser.open(ZENDESK_URL)
    
    print("\n=== INSTRUCCIONES ===")
    print("1. En el formulario de Zendesk:")
    print("   - Email: noemisanalex@hotmail.com")
    print("   - Subject: (ya copiado arriba)")
    print("   - Descripción: Ctrl+V para pegar el contenido")
    print("   - Categoría: SafePal Hardware Products")
    print("")
    print("2. Adjuntar archivos:")
    print("   - INT_Documento1791640661.pdf (denuncia Guardia Civil)")
    print("   - SafePal_Evidencia_OnChain.md")
    print("")
    print("3. Click Submit")
    print("")
    print("📁 Archivos en: C:\\Users\\Alejandro\\Desktop\\Caso_SafePal_Denuncia\\")

if __name__ == "__main__":
    main()
