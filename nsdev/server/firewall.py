import asyncio
import shutil

class FirewallManager:
    def __init__(self):
        self.has_ufw = shutil.which("ufw") is not None
        self.has_iptables = shutil.which("iptables") is not None

    async def _run_cmd(self, cmd):
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        return stdout.decode().strip(), stderr.decode().strip(), process.returncode

    async def ban_ip(self, ip_address):
        if self.has_ufw:
            stdout, stderr, code = await self._run_cmd(f"sudo ufw deny from {ip_address} to any")
            if code == 0:
                return f"Successfully banned {ip_address} using UFW."
            return f"UFW Error: {stderr}"
        
        if self.has_iptables:
            check_cmd = f"sudo iptables -C INPUT -s {ip_address} -j DROP"
            _, _, check_code = await self._run_cmd(check_cmd)
            if check_code == 0:
                return f"IP {ip_address} is already banned in iptables."

            stdout, stderr, code = await self._run_cmd(f"sudo iptables -A INPUT -s {ip_address} -j DROP")
            if code == 0:
                return f"Successfully banned {ip_address} using iptables."
            return f"IPTables Error: {stderr}"

        return "No supported firewall (ufw/iptables) found."

    async def unban_ip(self, ip_address):
        if self.has_ufw:
            stdout, stderr, code = await self._run_cmd(f"sudo ufw delete deny from {ip_address}")
            if code == 0:
                return f"Successfully unbanned {ip_address} using UFW."
            return f"UFW Error: {stderr}"

        if self.has_iptables:
            stdout, stderr, code = await self._run_cmd(f"sudo iptables -D INPUT -s {ip_address} -j DROP")
            if code == 0:
                return f"Successfully unbanned {ip_address} using iptables."
            return f"IPTables Error: {stderr}"

        return "No supported firewall found."

    async def list_banned(self):
        if self.has_ufw:
            stdout, _, _ = await self._run_cmd("sudo ufw status")
            return stdout

        if self.has_iptables:
            stdout, _, _ = await self._run_cmd("sudo iptables -L INPUT -n --line-numbers")
            return stdout

        return "No supported firewall found."
