import asyncio
import base64
import csv
import io
import os
import subprocess
import tempfile
from functools import partial
from types import SimpleNamespace
from typing import List, Optional

import httpx


class VPNGateClient:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.api_url = "https://www.vpngate.net/api/iphone/"
        self.country_code = "ID"

    async def _fetch_server_list(self) -> List[SimpleNamespace]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(self.api_url)
                response.raise_for_status()
                
                csv_data = response.text
                lines = csv_data.strip().split('\n')
                
                if len(lines) < 2:
                    raise ValueError("Invalid CSV data received from VPN Gate API")
                
                reader = csv.DictReader(lines[1:], delimiter=',')
                
                servers = []
                for row in reader:
                    if row.get('CountryShort') == self.country_code:
                        servers.append(SimpleNamespace(
                            hostname=row.get('HostName', ''),
                            ip=row.get('IP', ''),
                            score=int(row.get('Score', 0)),
                            ping=int(row.get('Ping', 999999)),
                            speed=int(row.get('Speed', 0)),
                            country_long=row.get('CountryLong', ''),
                            country_short=row.get('CountryShort', ''),
                            num_vpn_sessions=int(row.get('NumVpnSessions', 0)),
                            uptime=int(row.get('Uptime', 0)),
                            total_users=int(row.get('TotalUsers', 0)),
                            total_traffic=int(row.get('TotalTraffic', 0)),
                            log_type=row.get('LogType', ''),
                            operator=row.get('Operator', ''),
                            message=row.get('Message', ''),
                            config_data=row.get('OpenVPN_ConfigData_Base64', '')
                        ))
                
                return servers
                
            except httpx.RequestError as e:
                raise Exception(f"Failed to fetch VPN Gate server list: {e}")
            except Exception as e:
                raise Exception(f"Error parsing VPN Gate data: {e}")

    async def get_best_server(self) -> Optional[SimpleNamespace]:
        servers = await self._fetch_server_list()
        
        if not servers:
            return None
        
        servers_sorted = sorted(
            servers,
            key=lambda s: (-s.score, s.ping, -s.speed)
        )
        
        return servers_sorted[0] if servers_sorted else None

    async def get_all_servers(self) -> List[SimpleNamespace]:
        return await self._fetch_server_list()

    def _sync_create_ovpn_file(self, config_data: str, output_path: str) -> str:
        try:
            decoded_config = base64.b64decode(config_data).decode('utf-8')
            
            with open(output_path, 'w') as f:
                f.write(decoded_config)
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Failed to create OpenVPN config file: {e}")

    async def create_ovpn_file(self, config_data: str, output_path: str) -> str:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            partial(self._sync_create_ovpn_file, config_data, output_path)
        )

    def _sync_connect_vpn(self, ovpn_file_path: str, auth_file_path: Optional[str] = None) -> subprocess.Popen:
        if not os.path.exists(ovpn_file_path):
            raise FileNotFoundError(f"OpenVPN config file not found: {ovpn_file_path}")
        
        cmd = ["sudo", "openvpn", "--config", ovpn_file_path]
        
        if auth_file_path and os.path.exists(auth_file_path):
            cmd.extend(["--auth-user-pass", auth_file_path])
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return process
            
        except Exception as e:
            raise Exception(f"Failed to start OpenVPN process: {e}")

    async def connect_vpn(self, ovpn_file_path: str, auth_file_path: Optional[str] = None) -> subprocess.Popen:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            partial(self._sync_connect_vpn, ovpn_file_path, auth_file_path)
        )

    def _sync_disconnect_vpn(self, process: subprocess.Popen) -> bool:
        try:
            process.terminate()
            process.wait(timeout=10)
            return True
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            return True
        except Exception:
            return False

    async def disconnect_vpn(self, process: subprocess.Popen) -> bool:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            partial(self._sync_disconnect_vpn, process)
        )

    async def connect_to_best_server(self, output_dir: str = None) -> tuple:
        if output_dir is None:
            output_dir = tempfile.gettempdir()
        
        os.makedirs(output_dir, exist_ok=True)
        
        best_server = await self.get_best_server()
        
        if not best_server:
            raise Exception("No Indonesian VPN servers available")
        
        ovpn_path = os.path.join(output_dir, f"vpn_{best_server.hostname}.ovpn")
        
        await self.create_ovpn_file(best_server.config_data, ovpn_path)
        
        process = await self.connect_vpn(ovpn_path)
        
        return process, best_server, ovpn_path

    def _sync_check_connection(self) -> bool:
        try:
            result = subprocess.run(
                ["ip", "addr", "show", "tun0"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    async def check_connection(self) -> bool:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._sync_check_connection)

    async def get_current_ip(self) -> Optional[str]:
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                response = await client.get("https://api.ipify.org?format=json")
                response.raise_for_status()
                data = response.json()
                return data.get('ip')
            except Exception:
                return None

    def _sync_kill_all_openvpn(self) -> bool:
        try:
            subprocess.run(
                ["sudo", "killall", "openvpn"],
                capture_output=True,
                timeout=10
            )
            return True
        except Exception:
            return False

    async def kill_all_openvpn(self) -> bool:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._sync_kill_all_openvpn)


class VPNManager:
    def __init__(self, download_path: str = "downloads/vpn"):
        self.download_path = download_path
        self.vpn_client = VPNGateClient()
        self.current_process: Optional[subprocess.Popen] = None
        self.current_config_path: Optional[str] = None
        self.current_server: Optional[SimpleNamespace] = None
        
        os.makedirs(self.download_path, exist_ok=True)

    async def connect(self) -> SimpleNamespace:
        if self.current_process:
            await self.disconnect()
        
        original_ip = await self.vpn_client.get_current_ip()
        
        process, server, config_path = await self.vpn_client.connect_to_best_server(self.download_path)
        
        self.current_process = process
        self.current_config_path = config_path
        self.current_server = server
        
        await asyncio.sleep(5)
        
        connected = await self.vpn_client.check_connection()
        new_ip = await self.vpn_client.get_current_ip()
        
        return SimpleNamespace(
            success=connected,
            server=server,
            config_path=config_path,
            original_ip=original_ip,
            new_ip=new_ip,
            connected=connected
        )

    async def disconnect(self) -> bool:
        if not self.current_process:
            return True
        
        success = await self.vpn_client.disconnect_vpn(self.current_process)
        
        if success:
            self.current_process = None
            self.current_config_path = None
            self.current_server = None
        
        return success

    async def reconnect(self) -> SimpleNamespace:
        await self.disconnect()
        await asyncio.sleep(2)
        return await self.connect()

    async def get_status(self) -> SimpleNamespace:
        is_connected = False
        if self.current_process:
            is_connected = await self.vpn_client.check_connection()
        
        current_ip = await self.vpn_client.get_current_ip()
        
        return SimpleNamespace(
            connected=is_connected,
            current_ip=current_ip,
            server=self.current_server,
            config_path=self.current_config_path
        )

    async def list_servers(self, limit: Optional[int] = None) -> List[SimpleNamespace]:
        servers = await self.vpn_client.get_all_servers()
        
        if limit:
            return servers[:limit]
        
        return servers

    async def cleanup(self) -> bool:
        await self.disconnect()
        
        killed = await self.vpn_client.kill_all_openvpn()
        
        try:
            for file in os.listdir(self.download_path):
                if file.endswith('.ovpn'):
                    os.remove(os.path.join(self.download_path, file))
        except Exception:
            pass
        
        return killed

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
