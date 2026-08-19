# Valtus – OSINT & Google Dorking Tool

**Author:** [Excalibra](https://github.com/Excalibra)

Valtus is a graphical tool for ethical hacking, bug bounty, and OSINT research. It automates Google dorking with a clean, dark‑theme interface, integrated proxy/Tor support, and real‑time result categorisation.

## Features
- Enter a target domain or keyword and generate dorks instantly.
- Load predefined dork templates (website, people, socials).
- Use **Tor** or a custom proxy to bypass IP‑based rate limits.
- **Test One** button – run a single dork to verify connectivity.
- Real‑time results with category filtering and bulk open.
- Archive fetching via the Wayback Machine.
- All errors and progress logged in a dedicated console.

## Installation
```bash
git clone https://github.com/Excalibra/Valtus.git
cd Valtus
pip install -r requirements.txt
python main.py
