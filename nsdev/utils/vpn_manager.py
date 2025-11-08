import base64
import csv
from typing import Optional

import httpx


class VPNManager:
    VPN_GATE_URL = "https://www.vpngate.net/api/iphone/"

    async def _get_best_vpn_server(self, country_code: Optional[str] = None) -> Optional[dict]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.VPN_GATE_URL, timeout=20)
                response.raise_for_status()
        except httpx.RequestError:
            return None

        vpn_data = response.text
        if not vpn_data.strip():
            return None

        servers = []
        try:
            lines = vpn_data.split("\n")
            header_line = next(line for line in lines if line.startswith("#HostName"))
            header = header_line.strip().replace("#", "").split(",")

            csv_lines = [line for line in lines if not line.startswith(("*", "#")) and line.strip()]
            reader = csv.DictReader(csv_lines, fieldnames=header)
            servers = list(reader)
        except (StopIteration, csv.Error):
            return None

        if not servers:
            return None

        supported_servers = []
        for server in servers:
            try:
                if country_code and server.get("CountryShort", "").upper() != country_code.upper():
                    continue

                score = int(server.get("Score", "0"))
                ping = int(server.get("Ping", "9999"))
                if score > 100000 and ping < 200:
                    supported_servers.append(server)
            except (ValueError, TypeError):
                continue

        if not supported_servers:
            return None

        best_server = max(supported_servers, key=lambda s: int(s.get("Score", "0")))
        return best_server

    async def get_ovpn_config(self, country_code: Optional[str] = None) -> Optional[tuple[str, str]]:
        server = await self._get_best_vpn_server(country_code=country_code)
        if not server or "OpenVPN_ConfigData_Base64" not in server:
            return None

        try:
            ovpn_data_base64 = server["OpenVPN_ConfigData_Base64"]
            ovpn_config = base64.b64decode(ovpn_data_base64).decode("utf-8")

            modified_config = []
            for line in ovpn_config.splitlines():
                if line.startswith("remote "):
                    parts = line.split()
                    ip = server.get("IP")
                    port = parts[2]
                    protocol = parts[3]
                    modified_config.append(f"remote {ip} {port} {protocol}")
                else:
                    modified_config.append(line)

            final_config = "\n".join(modified_config)

            filename = f"vpngate_{server.get('CountryShort', 'INT')}_{server['IP']}.ovpn"
            return filename, final_config
        except (KeyError, base64.binascii.Error, UnicodeDecodeError):
            return None
