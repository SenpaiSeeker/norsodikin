class TelegramProgressBar:
    def __init__(self, client, message, task_name="Proses"):
        self.client = client
        self.message = message
        self.task_name = task_name
        self.time = __import__("time")
        self.start_time = self.time.time()
        self.last_update_time = 0
    
    def reset(self, new_task_name: str):
        self.task_name = new_task_name
        self.start_time = self.time.time()
        self.last_update_time = 0

    def _format_bytes(self, size):
        if not size:
            return "0B"
        power = 1024
        n = 0
        power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
        while size > power and n < len(power_labels) -1 :
            size /= power
            n += 1
        return f"{size:.2f} {power_labels[n]}B"

    async def update(self, current, total):
        current_time = self.time.time()
        if current_time - self.last_update_time < 2 and current < total:
            return
        self.last_update_time = current_time
        percentage = (current / total) * 100
        elapsed_time = current_time - self.start_time
        speed = current / elapsed_time if elapsed_time > 0 else 0
        progress_bar_length = 10
        filled_length = int(progress_bar_length * current // total)
        bar = '█' * filled_length + '░' * (progress_bar_length - filled_length)
        status_text = (
            f"**{self.task_name} sedang berjalan...**\n\n"
            f"`[{bar}] {percentage:.1f}%`\n\n"
            f"**Processed:** `{self._format_bytes(current)}` of `{self._format_bytes(total)}`\n"
            f"**Speed:** `{self._format_bytes(speed)}/s`\n"
        )
        try:
            await self.message.edit_text(status_text)
        except Exception:
            pass
