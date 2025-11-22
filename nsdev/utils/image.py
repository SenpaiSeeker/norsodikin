import asyncio
import base64
import random
import textwrap
from functools import partial
from io import BytesIO
from typing import Tuple

from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps
from playwright.async_api import async_playwright

from .font_manager import FontManager

try:
    from rembg import remove as remove_bg
except ImportError:
    remove_bg = None


class ImageManipulator(FontManager):
    def __init__(self):
        super().__init__()

    def _run_in_executor(self, func, *args, **kwargs):
        loop = asyncio.get_running_loop()
        return loop.run_in_executor(None, partial(func, *args, **kwargs))

    async def _render_html_with_playwright(
        self, 
        html_content: str, 
        selector: str = ".container", 
        scale_factor: float = 1.0, 
        width: int = 800, 
        height: int = 1000
    ) -> bytes:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(
                viewport={"width": width, "height": height},
                device_scale_factor=scale_factor
            )
            page = await context.new_page()
            await page.set_content(html_content)
            await page.wait_for_load_state("networkidle")

            element_handle = await page.query_selector(selector)
            if not element_handle:
                await browser.close()
                raise RuntimeError(f"Could not find the '{selector}' element to screenshot.")

            screenshot_bytes = await element_handle.screenshot(type="png", omit_background=True)
            await browser.close()
            return screenshot_bytes

    async def create_fake_tweet(
        self,
        pfp_bytes: bytes,
        name: str,
        username: str,
        text: str,
        time_str: str,
        date_str: str,
        stats: dict,
    ) -> bytes:
        if pfp_bytes:
            pfp_base64 = "data:image/png;base64," + base64.b64encode(pfp_bytes).decode()
        else:
            initial = name[0].upper() if name else "U"
            default_pfp_bytes = self._get_default_pfp(initial)
            pfp_base64 = "data:image/png;base64," + base64.b64encode(default_pfp_bytes).decode()

        svg_verified = '<svg viewBox="0 0 22 22" width="20" height="20"><g><path d="M20.396 11c-.018-.646-.215-1.275-.57-1.816-.354-.54-.852-.972-1.438-1.246.223-.603.27-1.264.14-1.897-.131-.634-.437-1.218-.882-1.687-.47-.445-1.053-.75-1.687-.882-.633-.13-1.294-.083-1.897.14-.273-.587-.704-1.086-1.245-1.44S11.647 1.62 11 1.604c-.646.017-1.273.213-1.813.568s-.969.854-1.24 1.44c-.604-.223-1.264-.27-1.896-.14-.635.13-1.218.436-1.687.882-.445.468-.751 1.053-.882 1.687-.13.633-.083 1.294.14 1.897-.587.273-1.086.705-1.44 1.245-.354.54-.55 1.17-.569 1.816.017.647.215 1.276.568 1.817.354.54.853.972 1.44 1.245-.224.604-.27 1.264-.14 1.896.13.635.436 1.219.882 1.687.468.445 1.053.75 1.687.882.633.13 1.294.083 1.897-.14.273.587.705 1.086 1.245 1.44.54.354 1.17.55 1.816.569.647-.016 1.276-.214 1.817-.568.54-.354.972-.853 1.245-1.44.604.224 1.264.27 1.896.14.635-.13 1.219-.436 1.687-.882.445-.468.75-1.053.882-1.687.13-.633.083-1.294-.14-1.897.587-.273 1.086-.705 1.44-1.245.355-.54.55-1.17.569-1.816zM9.662 14.85l-3.429-3.428 1.293-1.302 2.072 2.072 4.4-4.794 1.347 1.246z" fill="#1d9bf0"></path></g></svg>'

        html_template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');
                
                body {{
                    margin: 0;
                    padding: 0;
                    background: transparent;
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                }}
                
                .tweet-card {{
                    background-color: #000000;
                    color: #e7e9ea;
                    padding: 30px;
                    width: 700px;
                    box-sizing: border-box;
                    display: inline-block;
                }}
                
                .header {{
                    display: flex;
                    align-items: flex-start;
                    margin-bottom: 15px;
                }}
                
                .pfp {{
                    width: 56px;
                    height: 56px;
                    border-radius: 50%;
                    object-fit: cover;
                    margin-right: 12px;
                }}
                
                .user-info {{
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    margin-top: 4px;
                }}
                
                .name-row {{
                    display: flex;
                    align-items: center;
                    gap: 4px;
                }}
                
                .name {{
                    font-weight: 700;
                    font-size: 17px;
                    color: #e7e9ea;
                    line-height: 20px;
                }}
                
                .username {{
                    color: #71767b;
                    font-size: 16px;
                    line-height: 20px;
                }}
                
                .content {{
                    font-size: 26px;
                    line-height: 1.4;
                    margin-top: 10px;
                    margin-bottom: 20px;
                    white-space: pre-wrap;
                    color: #e7e9ea;
                    font-weight: 400;
                }}
                
                .meta {{
                    color: #71767b;
                    font-size: 16px;
                    margin-bottom: 15px;
                    padding-bottom: 15px;
                    border-bottom: 1px solid #2f3336;
                    display: flex;
                    gap: 6px;
                    align-items: center;
                    font-weight: 500;
                }}
                
                .views-container {{
                    display: flex;
                    align-items: center;
                    gap: 4px;
                    margin-left: auto; 
                }}
                
                .stats {{
                    display: flex;
                    gap: 24px;
                    color: #71767b;
                    font-size: 16px;
                    padding-bottom: 8px;
                    margin-bottom: 0;
                }}
                
                .stat-item strong {{
                    color: #e7e9ea;
                    font-weight: 700;
                }}
            </style>
        </head>
        <body>
            <div class="tweet-card">
                <div class="header">
                    <img src="{pfp_base64}" class="pfp" />
                    <div class="user-info">
                        <div class="name-row">
                            <span class="name">{name}</span>
                            {svg_verified}
                        </div>
                        <span class="username">@{username}</span>
                    </div>
                </div>
                <div class="content">{text}</div>
                <div class="meta">
                    <span>{time_str}</span> · <span>{date_str}</span>
                    <div class="views-container">
                         <span style="font-weight: 700; color: #e7e9ea;">{views}</span>
                         <span>Views</span>
                    </div>
                </div>
                <div class="stats">
                    <div class="stat-item"><strong>{retweets}</strong> Retweets</div>
                    <div class="stat-item"><strong>{quotes}</strong> Quotes</div>
                    <div class="stat-item"><strong>{likes}</strong> Likes</div>
                    <div class="stat-item"><strong>{bookmarks}</strong> Bookmarks</div>
                </div>
            </div>
        </body>
        </html>
        """.format(
            pfp_base64=pfp_base64,
            name=name,
            svg_verified=svg_verified,
            username=username,
            text=text,
            time_str=time_str,
            date_str=date_str,
            views=stats.get("views", "0"),
            retweets=stats.get("retweets", "0"),
            quotes=stats.get("quotes", "0"),
            likes=stats.get("likes", "0"),
            bookmarks=stats.get("bookmarks", "0")
        )

        return await self._render_html_with_playwright(
            html_content=html_template, 
            selector=".tweet-card", 
            scale_factor=3.0, 
            width=700, 
            height=800
        )

    async def create_fake_ig_post(
        self,
        pfp_bytes: bytes,
        name: str,
        post_bytes: bytes,
        caption: str,
        likes: str,
        time_ago: str,
    ) -> bytes:
        if pfp_bytes:
            pfp_base64 = "data:image/png;base64," + base64.b64encode(pfp_bytes).decode()
        else:
            initial = name[0].upper() if name else "U"
            default_pfp_bytes = self._get_default_pfp(initial)
            pfp_base64 = "data:image/png;base64," + base64.b64encode(default_pfp_bytes).decode()

        post_base64 = "data:image/png;base64," + base64.b64encode(post_bytes).decode()

        svg_verified = '<svg viewBox="0 0 22 22" width="20" height="20"><g><path d="M20.396 11c-.018-.646-.215-1.275-.57-1.816-.354-.54-.852-.972-1.438-1.246.223-.603.27-1.264.14-1.897-.131-.634-.437-1.218-.882-1.687-.47-.445-1.053-.75-1.687-.882-.633-.13-1.294-.083-1.897.14-.273-.587-.704-1.086-1.245-1.44S11.647 1.62 11 1.604c-.646.017-1.273.213-1.813.568s-.969.854-1.24 1.44c-.604-.223-1.264-.27-1.896-.14-.635.13-1.218.436-1.687.882-.445.468-.751 1.053-.882 1.687-.13.633-.083 1.294.14 1.897-.587.273-1.086.705-1.44 1.245-.354.54-.55 1.17-.569 1.816.017.647.215 1.276.568 1.817.354.54.853.972 1.44 1.245-.224.604-.27 1.264-.14 1.896.13.635.436 1.219.882 1.687.468.445 1.053.75 1.687.882.633.13 1.294.083 1.897-.14.273.587.705 1.086 1.245 1.44.54.354 1.17.55 1.816.569.647-.016 1.276-.214 1.817-.568.54-.354.972-.853 1.245-1.44.604.224 1.264.27 1.896.14.635-.13 1.219-.436 1.687-.882.445-.468.75-1.053.882-1.687.13-.633.083-1.294-.14-1.897.587-.273 1.086-.705 1.44-1.245.355-.54.55-1.17.569-1.816zM9.662 14.85l-3.429-3.428 1.293-1.302 2.072 2.072 4.4-4.794 1.347 1.246z" fill="#1d9bf0"></path></g></svg>'
        svg_more = '<svg aria-label="More options" fill="#ffffff" height="24" role="img" viewBox="0 0 24 24" width="24"><circle cx="12" cy="12" r="1.5"></circle><circle cx="6" cy="12" r="1.5"></circle><circle cx="18" cy="12" r="1.5"></circle></svg>'
        svg_like = '<svg aria-label="Like" fill="#ffffff" height="24" role="img" viewBox="0 0 24 24" width="24"><path d="M16.792 3.904A4.989 4.989 0 0 1 21.5 9.122c0 3.072-2.652 4.959-5.197 7.222-2.512 2.243-3.865 3.469-4.303 3.752-.477-.309-2.143-1.823-4.303-3.752C5.141 14.072 2.5 12.167 2.5 9.122a4.989 4.989 0 0 1 4.708-5.218 4.21 4.21 0 0 1 3.675 1.941c.84 1.175.98 1.763 1.12 1.763s.278-.588 1.11-1.766a4.17 4.17 0 0 1 3.679-1.938m0-2a6.04 6.04 0 0 0-4.797 2.127 6.052 6.052 0 0 0-4.787-2.127A6.985 6.985 0 0 0 .5 9.122c0 3.61 2.55 5.827 5.015 7.97.283.246.569.494.853.747l1.027.918a44.998 44.998 0 0 0 3.518 3.018 2 2 0 0 0 2.174 0 45.263 45.263 0 0 0 3.626-3.115l.922-.824c.293-.26.59-.519.885-.774 2.334-2.025 4.98-4.32 4.98-7.94a6.985 6.985 0 0 0-6.708-7.218Z"></path></svg>'
        svg_comment = '<svg aria-label="Comment" fill="#ffffff" height="24" role="img" viewBox="0 0 24 24" width="24"><path d="M20.656 17.008a9.993 9.993 0 1 0-3.59 3.615L22 22Z" fill="none" stroke="#ffffff" stroke-linejoin="round" stroke-width="2"></path></svg>'
        svg_share = '<svg aria-label="Share Post" fill="#ffffff" height="24" role="img" viewBox="0 0 24 24" width="24"><line fill="none" stroke="#ffffff" stroke-linejoin="round" stroke-width="2" x1="22" x2="9.218" y1="2" y2="10.083"></line><polygon fill="none" points="11.698 20.334 22 3.001 2 3.001 9.218 10.084 11.698 20.334" stroke="#ffffff" stroke-linejoin="round" stroke-width="2"></polygon></svg>'
        svg_save = '<svg aria-label="Save" fill="#ffffff" height="24" role="img" viewBox="0 0 24 24" width="24"><polygon fill="none" points="20 21 12 13.44 4 21 4 3 20 3 20 21" stroke="#ffffff" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></polygon></svg>'

        html_template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
                
                body {{
                    margin: 0;
                    padding: 0;
                    background: transparent;
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                }}
                
                .ig-card {{
                    background-color: #000000;
                    color: #ffffff;
                    width: 600px;
                    box-sizing: border-box;
                    display: inline-block;
                    border: 1px solid #262626;
                    border-radius: 8px;
                    overflow: hidden;
                }}
                
                .header {{
                    display: flex;
                    align-items: center;
                    padding: 14px;
                    border-bottom: 1px solid #262626;
                }}
                
                .pfp {{
                    width: 32px;
                    height: 32px;
                    border-radius: 50%;
                    object-fit: cover;
                    margin-right: 10px;
                    border: 1px solid #262626;
                }}
                
                .username-container {{
                    flex-grow: 1;
                    display: flex;
                    align-items: center;
                    gap: 4px;
                }}

                .username {{
                    font-weight: 600;
                    font-size: 14px;
                }}
                
                .post-image {{
                    width: 100%;
                    height: auto;
                    display: block;
                    max-height: 750px; 
                    object-fit: cover;
                }}
                
                .actions {{
                    padding: 12px 14px 0 14px;
                    display: flex;
                    align-items: center;
                }}
                
                .icon-group {{
                    display: flex;
                    gap: 16px;
                    margin-right: auto;
                }}
                
                .likes {{
                    padding: 0 14px;
                    margin-top: 10px;
                    font-weight: 600;
                    font-size: 14px;
                }}
                
                .caption-area {{
                    padding: 8px 14px;
                    font-size: 14px;
                    line-height: 1.45;
                }}
                
                .caption-user {{
                    font-weight: 600;
                    margin-right: 5px;
                }}
                
                .time-ago {{
                    padding: 0 14px 14px 14px;
                    font-size: 12px;
                    color: #a8a8a8;
                    text-transform: uppercase;
                }}
            </style>
        </head>
        <body>
            <div class="ig-card">
                <div class="header">
                    <img src="{pfp_base64}" class="pfp" />
                    <div class="username-container">
                        <span class="username">{name}</span>
                        {svg_verified}
                    </div>
                    {svg_more}
                </div>
                
                <img src="{post_base64}" class="post-image" />
                
                <div class="actions">
                    <div class="icon-group">
                        {svg_like}
                        {svg_comment}
                        {svg_share}
                    </div>
                    {svg_save}
                </div>
                
                <div class="likes">{likes} likes</div>
                
                <div class="caption-area">
                    <span class="caption-user">{name}</span>
                    <span class="caption-text">{caption}</span>
                </div>
                
                <div class="time-ago">{time_ago} AGO</div>
            </div>
        </body>
        </html>
        """.format(
            pfp_base64=pfp_base64,
            name=name,
            post_base64=post_base64,
            svg_verified=svg_verified,
            svg_more=svg_more,
            svg_like=svg_like,
            svg_comment=svg_comment,
            svg_share=svg_share,
            svg_save=svg_save,
            likes=likes,
            caption=caption,
            time_ago=time_ago
        )

        return await self._render_html_with_playwright(
            html_content=html_template, 
            selector=".ig-card", 
            scale_factor=3.0, 
            width=650, 
            height=1200
        )

    async def create_fake_wa_chat(
        self,
        pfp_bytes: bytes,
        name: str,
        message: str,
        time_str: str,
    ) -> bytes:
        if pfp_bytes:
            pfp_base64 = "data:image/png;base64," + base64.b64encode(pfp_bytes).decode()
        else:
            initial = name[0].upper() if name else "U"
            default_pfp_bytes = self._get_default_pfp(initial)
            pfp_base64 = "data:image/png;base64," + base64.b64encode(default_pfp_bytes).decode()

        svg_back = '<svg viewBox="0 0 24 24" width="24" height="24"><path fill="#aebac1" d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"></path></svg>'
        svg_video = '<svg viewBox="0 0 24 24" width="24" height="24"><path fill="#aebac1" d="M17 10.5V7c0-.55-.45-1-1-1H4c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h12c.55 0 1-.45 1-1v-3.5l4 4v-11l-4 4z"></path></svg>'
        svg_call = '<svg viewBox="0 0 24 24" width="24" height="24"><path fill="#aebac1" d="M20.01 15.38c-1.23 0-2.42-.2-3.53-.56-.35-.12-.74-.03-1.01.24l-1.57 1.97c-2.83-1.44-5.15-3.75-6.59-6.59l1.97-1.57c.26-.27.36-.66.24-1.01-.37-1.11-.56-2.3-.56-3.53 0-.55-.45-1-1-1H4.39c-.55 0-1 .45-1 1 0 9.39 7.61 17 17 17 .55 0 1-.45 1-1v-4.61c0-.55-.45-1-1-1z"></path></svg>'
        svg_more = '<svg viewBox="0 0 24 24" width="24" height="24"><path fill="#aebac1" d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"></path></svg>'
        svg_smiley = '<svg viewBox="0 0 24 24" width="26" height="26"><path fill="#8696a0" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm3.5-9c.83 0 1.5-.67 1.5-1.5S16.33 8 15.5 8 14 8.67 14 9.5s.67 1.5 1.5 1.5zm-7 0c.83 0 1.5-.67 1.5-1.5S9.33 8 8.5 8 7 8.67 7 9.5 7.67 11 8.5 11zm3.5 6.5c2.33 0 4.31-1.46 5.11-3.5H6.89c.8 2.04 2.78 3.5 5.11 3.5z"></path></svg>'
        svg_attach = '<svg viewBox="0 0 24 24" width="24" height="24"><path fill="#8696a0" d="M16.5 6v11.5c0 2.21-1.79 4-4 4s-4-1.79-4-4V5a2.5 2.5 0 0 1 5 0v10.5c0 .55-.45 1-1 1s-1-.45-1-1V6H10v9.5a2.5 2.5 0 0 0 5 0V5c0-2.21-1.79-4-4-4S7 2.79 7 5v12.5c0 3.04 2.46 5.5 5.5 5.5s5.5-2.46 5.5-5.5V6h-1.5z"></path></svg>'
        svg_cam = '<svg viewBox="0 0 24 24" width="24" height="24"><path fill="#8696a0" d="M12 15c1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3 1.34 3 3 3zm7-8h-1.5v-.5c0-1.38-1.12-2.5-2.5-2.5H9c-1.38 0-2.5 1.12-2.5 2.5v.5H5c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V9c0-1.1-.9-2-2-2zm-7 12c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5z"></path></svg>'
        svg_mic = '<svg viewBox="0 0 24 24" width="24" height="24"><path fill="#00a884" d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"></path><path fill="#00a884" d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"></path></svg>'

        html_template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Helvetica+Now+Text:wght@400;500&display=swap');
                
                body {{
                    margin: 0;
                    padding: 0;
                    background: transparent;
                    font-family: 'Helvetica Now Text', Helvetica, Arial, sans-serif;
                }}
                
                .wa-container {{
                    width: 500px;
                    height: 900px;
                    background-color: #0b141a;
                    background-image: url('https://i.imgur.com/4801n6r.png'); 
                    background-repeat: repeat;
                    background-size: 400px;
                    display: flex;
                    flex-direction: column;
                    position: relative;
                    overflow: hidden;
                }}
                
                .header {{
                    background-color: #1f2c34;
                    padding: 10px 16px;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    height: 60px;
                    z-index: 10;
                }}
                
                .pfp {{
                    width: 40px;
                    height: 40px;
                    border-radius: 50%;
                    object-fit: cover;
                }}
                
                .user-info {{
                    flex-grow: 1;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                }}
                
                .name {{
                    color: #e9edef;
                    font-size: 16px;
                    font-weight: 500;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }}
                
                .status {{
                    color: #8696a0;
                    font-size: 13px;
                }}
                
                .icons {{
                    display: flex;
                    gap: 20px;
                }}
                
                .chat-area {{
                    flex-grow: 1;
                    padding: 20px;
                    display: flex;
                    flex-direction: column;
                    justify-content: flex-end; 
                }}
                
                .message-bubble {{
                    background-color: #1f2c34;
                    color: #e9edef;
                    padding: 10px 14px;
                    border-radius: 0px 12px 12px 12px;
                    max-width: 75%;
                    align-self: flex-start;
                    position: relative;
                    box-shadow: 0 1px 0.5px rgba(0,0,0,0.13);
                    margin-bottom: 10px;
                }}
                
                .message-bubble::before {{
                    content: "";
                    position: absolute;
                    top: 0;
                    left: -8px;
                    width: 0;
                    height: 0;
                    border: 8px solid transparent;
                    border-top-color: #1f2c34;
                    border-right-color: #1f2c34;
                    border-bottom: 0;
                }}
                
                .message-text {{
                    font-size: 16px;
                    line-height: 1.4;
                }}
                
                .message-time {{
                    font-size: 11px;
                    color: #8696a0;
                    float: right;
                    margin-left: 10px;
                    margin-top: 6px;
                    position: relative;
                    top: 4px;
                }}
                
                .footer {{
                    background-color: #1f2c34;
                    padding: 10px;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    height: 62px;
                }}
                
                .input-box {{
                    flex-grow: 1;
                    background-color: #2a3942;
                    border-radius: 8px;
                    height: 40px;
                    display: flex;
                    align-items: center;
                    padding: 0 12px;
                    color: #8696a0;
                    font-size: 15px;
                }}

                .mic-circle {{
                    background-color: #00a884;
                    width: 48px;
                    height: 48px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    display: none; 
                }}
                
            </style>
        </head>
        <body>
            <div class="wa-container">
                <div class="header">
                    {svg_back}
                    <img src="{pfp_base64}" class="pfp" />
                    <div class="user-info">
                        <div class="name">{name}</div>
                        <div class="status">online</div>
                    </div>
                    <div class="icons">
                        {svg_video}
                        {svg_call}
                        {svg_more}
                    </div>
                </div>
                
                <div class="chat-area">
                    <div class="message-bubble">
                        <div class="message-text">{message}</div>
                        <div class="message-time">{time_str}</div>
                    </div>
                </div>
                
                <div class="footer">
                    {svg_smiley}
                    <div class="input-box">Message</div>
                    {svg_attach}
                    {svg_cam}
                    {svg_mic}
                </div>
            </div>
        </body>
        </html>
        """.format(
            pfp_base64=pfp_base64,
            name=name,
            message=message,
            time_str=time_str,
            svg_back=svg_back,
            svg_video=svg_video,
            svg_call=svg_call,
            svg_more=svg_more,
            svg_smiley=svg_smiley,
            svg_attach=svg_attach,
            svg_cam=svg_cam,
            svg_mic=svg_mic
        )

        return await self._render_html_with_playwright(
            html_content=html_template, 
            selector=".wa-container", 
            scale_factor=3.0, 
            width=500, 
            height=900
        )

    def _sync_create_quote(self, text: str, user_name: str, pfp_bytes: bytes, invert: bool, message_obj) -> bytes:
        return asyncio.run(self._async_create_quote(text, user_name, pfp_bytes, invert, message_obj))

    async def _async_create_quote(self, text: str, user_name: str, pfp_bytes: bytes, invert: bool, message_obj=None) -> bytes:
        if pfp_bytes:
            pfp_base64 = "data:image/png;base64," + base64.b64encode(pfp_bytes).decode()
        else:
            initial = user_name[0].upper() if user_name else "U"
            default_pfp_bytes = self._get_default_pfp(initial)
            pfp_base64 = "data:image/png;base64," + base64.b64encode(default_pfp_bytes).decode()

        bg_color, text_color, name_color = (
            ("transparent", "#FFFFFF", "#AAAAAA") if not invert else ("transparent", "#161616", "#555555")
        )
        link_color = "#88C0D0" if not invert else "#3B82F6"

        final_text = text
        if message_obj and message_obj.entities:
            final_text_list = []
            last_offset = 0
            entities = sorted(message_obj.entities, key=lambda e: e.offset)
            
            for entity in entities:
                if entity.offset > last_offset:
                    final_text_list.append(text[last_offset:entity.offset])
                
                chunk = text[entity.offset:entity.offset + entity.length]
                if entity.type.name == "CUSTOM_EMOJI":
                    emoji_id = str(entity.custom_emoji_id)
                    emoji_url = f"https://cdn.jsdelivr.net/gh/Telegram/CustomEmoji@{emoji_id}/emoji.png" 
                    final_text_list.append(f'<img src="{emoji_url}" style="width:1.2em;height:1.2em;vertical-align:middle;" onerror="this.style.display=\'none\'">')
                else:
                    final_text_list.append(chunk)
                
                last_offset = entity.offset + entity.length
            
            if last_offset < len(text):
                final_text_list.append(text[last_offset:])
            
            final_text = "".join(final_text_list)
        
        soup = BeautifulSoup(final_text, "html.parser")
        for tag in soup.find_all("a"):
            tag.name = "span"
            tag["style"] = f"color: {link_color};"

        clean_html = str(soup).replace("\n", "<br>")

        html_template = """
        <html>
        <head>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;700&display=swap');
                body {{
                    margin: 0;
                    display: inline-block;
                }}
                .container {{
                    font-family: 'Noto Sans', sans-serif;
                    background: {bg_color};
                    color: {text_color};
                    padding: 40px;
                    display: flex;
                    align-items: flex-start;
                    min-width: 400px;
                    max-width: 1200px;
                }}
                .pfp {{
                    width: 100px;
                    height: 100px;
                    border-radius: 50%;
                    object-fit: cover;
                    margin-right: 25px;
                    flex-shrink: 0;
                }}
                .text-content {{
                    display: flex;
                    flex-direction: column;
                }}
                .name {{
                    font-size: 28px;
                    font-weight: 700;
                    color: {name_color};
                    margin-bottom: 10px;
                }}
                .quote {{
                    font-size: 36px;
                    line-height: 1.4;
                    word-wrap: break-word;
                    word-break: break-all;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <img src="{pfp_base64}" class="pfp" />
                <div class="text-content">
                    <div class="name">{user_name}</div>
                    <div class="quote">{clean_html}</div>
                </div>
            </div>
        </body>
        </html>
        """.format(
            bg_color=bg_color,
            text_color=text_color,
            name_color=name_color,
            pfp_base64=pfp_base64,
            user_name=user_name,
            clean_html=clean_html,
        )

        return await self._render_html_with_playwright(html_content=html_template, selector=".container")

    async def create_quote(self, text: str, user_name: str, pfp_bytes: bytes, invert: bool = False, message_obj=None) -> bytes:
        return await self._async_create_quote(text, user_name, pfp_bytes, invert, message_obj)

    def _sync_add_watermark(
        self,
        image_bytes: bytes,
        text: str,
        position: Tuple[int, int] = (10, 10),
        font_size: int = 30,
        opacity: int = 128,
    ) -> bytes:
        img = Image.open(BytesIO(image_bytes)).convert("RGBA")
        txt_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))

        font_size = int(img.width / 15)
        font = self._get_font(font_size)
        draw = ImageDraw.Draw(txt_layer)

        random_color = (random.randint(150, 255), random.randint(150, 255), random.randint(150, 255), opacity)
        outline_color = (0, 0, 0, opacity)

        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        x = (img.width - text_width) / 2
        y = (img.height - text_height) / 2

        for offset_x in range(-2, 3):
            for offset_y in range(-2, 3):
                if offset_x != 0 or offset_y != 0:
                    draw.text((x + offset_x, y + offset_y), text, font=font, fill=outline_color)

        draw.text((x, y), text, font=font, fill=random_color)

        watermarked_img = Image.alpha_composite(img, txt_layer)
        output_buffer = BytesIO()
        watermarked_img.save(output_buffer, format="PNG")
        return output_buffer.getvalue()

    async def add_watermark(
        self,
        image_bytes: bytes,
        text: str,
        position: Tuple[int, int] = (10, 10),
        font_size: int = 30,
        opacity: int = 200,
    ) -> bytes:
        return await self._run_in_executor(self._sync_add_watermark, image_bytes, text, position, font_size, opacity)

    def _sync_resize(self, image_bytes: bytes, size: Tuple[int, int], keep_aspect_ratio: bool = True) -> bytes:
        img = Image.open(BytesIO(image_bytes))
        if keep_aspect_ratio:
            img.thumbnail(size, Image.Resampling.LANCZOS)
        else:
            img = img.resize(size, Image.Resampling.LANCZOS)
        output_buffer = BytesIO()
        output_format = img.format if img.format in ["JPEG", "PNG", "WEBP"] else "PNG"
        img.save(output_buffer, format=output_format)
        return output_buffer.getvalue()

    async def resize(self, image_bytes: bytes, size: Tuple[int, int], keep_aspect_ratio: bool = True) -> bytes:
        return await self._run_in_executor(self._sync_resize, image_bytes, size, keep_aspect_ratio)

    def _sync_convert_format(self, image_bytes: bytes, output_format: str = "PNG") -> bytes:
        img = Image.open(BytesIO(image_bytes))
        if img.mode == "RGBA" and output_format.upper() == "JPEG":
            img = img.convert("RGB")
        output_buffer = BytesIO()
        img.save(output_buffer, format=output_format.upper())
        return output_buffer.getvalue()

    async def convert_format(self, image_bytes: bytes, output_format: str = "PNG") -> bytes:
        return await self._run_in_executor(self._sync_convert_format, image_bytes, output_format)

    def _sync_create_meme(self, image_bytes: bytes, top_text: str, bottom_text: str) -> bytes:
        img = Image.open(BytesIO(image_bytes)).convert("RGBA")
        draw = ImageDraw.Draw(img)
        font_size = int(img.width / 10)
        font = self._get_font(font_size)

        def draw_text_with_outline(text, x, y):
            outline_color, text_color = "black", "white"
            for offset in [(-2, -2), (2, -2), (-2, 2), (2, 2)]:
                draw.text((x + offset[0], y + offset[1]), text, font=font, fill=outline_color)
            draw.text((x, y), text, font=font, fill=text_color)

        top_text, bottom_text = top_text.upper(), bottom_text.upper()

        if top_text:
            bbox = draw.textbbox((0, 0), top_text, font=font)
            top_w = bbox[2] - bbox[0]
            draw_text_with_outline(top_text, (img.width - top_w) / 2, 10)
        if bottom_text:
            bbox = draw.textbbox((0, 0), bottom_text, font=font)
            bottom_w, bottom_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            draw_text_with_outline(bottom_text, (img.width - bottom_w) / 2, img.height - bottom_h - 15)

        output_buffer = BytesIO()
        img.save(output_buffer, format="PNG")
        return output_buffer.getvalue()

    async def create_meme(self, image_bytes: bytes, top_text: str, bottom_text: str) -> bytes:
        return await self._run_in_executor(self._sync_create_meme, image_bytes, top_text, bottom_text)

    def _sync_apply_filter(self, image_bytes: bytes, filter_name: str) -> bytes:
        img = Image.open(BytesIO(image_bytes)).convert("RGB")
        if filter_name == "grayscale":
            processed_img = ImageOps.grayscale(img)
        elif filter_name == "sepia":
            grayscale_img = ImageOps.grayscale(img)
            sepia_palette = [
                component
                for i in range(256)
                for component in (int(min(255, i * 1.2)), int(min(255, i * 1.0)), int(min(255, i * 0.8)))
            ]
            grayscale_img.putpalette(sepia_palette)
            grayscale_img = grayscale_img.convert("RGB")
            processed_img = grayscale_img
        elif filter_name == "invert":
            processed_img = ImageOps.invert(img)
        elif filter_name == "blur":
            processed_img = img.filter(ImageFilter.GaussianBlur(radius=5))
        elif filter_name == "sharpen":
            processed_img = img.filter(ImageFilter.SHARPEN)
        elif filter_name == "hell":
            enhancer = ImageEnhance.Contrast(img)
            img_contrasted = enhancer.enhance(1.5)
            img_gray = ImageOps.grayscale(img_contrasted)
            processed_img = ImageOps.colorize(img_gray, black=(20, 0, 0), mid=(200, 50, 0), white=(255, 220, 50))
        else:
            raise ValueError(f"Filter '{filter_name}' tidak dikenal.")
        output_buffer = BytesIO()
        processed_img.save(output_buffer, format="JPEG")
        return output_buffer.getvalue()

    async def apply_filter(self, image_bytes: bytes, filter_name: str) -> bytes:
        return await self._run_in_executor(self._sync_apply_filter, image_bytes, filter_name)

    def _sync_remove_background(self, image_bytes: bytes) -> bytes:
        if not remove_bg:
            raise ImportError("Pustaka 'rembg' tidak terinstal. Silakan instal dengan `pip install norsodikin[ai]`")
        return remove_bg(image_bytes)

    async def remove_background(self, image_bytes: bytes) -> bytes:
        return await self._run_in_executor(self._sync_remove_background, image_bytes)

    def _sync_convert_sticker_to_png(self, sticker_bytes: bytes) -> bytes:
        img = Image.open(BytesIO(sticker_bytes))
        output_buffer = BytesIO()
        img.save(output_buffer, format="PNG")
        return output_buffer.getvalue()

    async def convert_sticker_to_png(self, sticker_bytes: bytes) -> bytes:
        return await self._run_in_executor(self._sync_convert_sticker_to_png, sticker_bytes)

    def _get_default_pfp(self, initial: str) -> bytes:
        W, H = (200, 200)
        bg_color = (120, 120, 120)
        img = Image.new("RGB", (W, H), color=bg_color)

        font = self._get_font(100)
        draw = ImageDraw.Draw(img)

        bbox = draw.textbbox((0, 0), initial, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        position = ((W - text_w) / 2, (H - text_h) / 2 - 10)
        draw.text(position, initial, font=font, fill=(255, 255, 255))

        output = BytesIO()
        img.save(output, format="PNG")
        return output.getvalue()

    def _sync_deepfry(self, image_bytes: bytes) -> bytes:
        img = Image.open(BytesIO(image_bytes)).convert("RGB")
        img = ImageEnhance.Color(img).enhance(3.0)
        img = ImageEnhance.Contrast(img).enhance(2.5)
        img = ImageEnhance.Sharpness(img).enhance(3.0)

        noise = Image.new("RGB", img.size)
        draw = ImageDraw.Draw(noise)
        for y in range(img.height):
            for x in range(img.width):
                draw.point((x, y), (random.randint(0, 50), random.randint(0, 50), random.randint(0, 50)))
        img = Image.blend(img, noise, 0.15)

        output_buffer = BytesIO()
        img.save(output_buffer, format="JPEG", quality=80)
        return output_buffer.getvalue()

    async def deepfry(self, image_bytes: bytes) -> bytes:
        return await self._run_in_executor(self._sync_deepfry, image_bytes)

    def _sync_create_afk_card(self, pfp_bytes: bytes, name: str, reason: str, duration: str) -> bytes:
        return asyncio.run(self._async_create_afk_card(pfp_bytes, name, reason, duration))

    async def _async_create_afk_card(self, pfp_bytes: bytes, name: str, reason: str, duration: str) -> bytes:
        if pfp_bytes:
            pfp_base64 = "data:image/png;base64," + base64.b64encode(pfp_bytes).decode()
        else:
            initial = name[0].upper() if name else "U"
            default_pfp_bytes = self._get_default_pfp(initial)
            pfp_base64 = "data:image/png;base64," + base64.b64encode(default_pfp_bytes).decode()

        reason_html = f'<div class="detail">Alasan: {reason}</div>' if reason else ""

        html_template = """
        <html>
        <head>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;700&display=swap');
                body {{
                    margin: 0;
                    display: inline-block;
                }}
                .container {{
                    font-family: 'Noto Sans', sans-serif;
                    background: #1C1C1E;
                    padding: 40px;
                    display: flex;
                    align-items: center;
                }}
                .pfp {{
                    width: 128px;
                    height: 128px;
                    border-radius: 50%;
                    object-fit: cover;
                    margin-right: 30px;
                    flex-shrink: 0;
                }}
                .text-content {{
                    display: flex;
                    flex-direction: column;
                }}
                .name {{
                    font-size: 36px;
                    font-weight: 700;
                    color: #FFFFFF;
                }}
                .status {{
                    font-size: 28px;
                    font-weight: 700;
                    color: #FF9500;
                    margin-top: 5px;
                }}
                .detail {{
                    font-size: 24px;
                    color: #EBEBF599;
                    margin-top: 15px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <img src="{pfp_base64}" class="pfp" />
                <div class="text-content">
                    <div class="name">{name}</div>
                    <div class="status">SEDANG AFK</div>
                    {reason_html}
                    <div class="detail">Sejak: {duration}</div>
                </div>
            </div>
        </body>
        </html>
        """.format(
            pfp_base64=pfp_base64,
            name=name,
            reason_html=reason_html,
            duration=duration,
        )

        return await self._render_html_with_playwright(html_content=html_template, selector=".container")

    async def create_afk_card(self, pfp_bytes: bytes, name: str, reason: str, duration: str) -> bytes:
        return await self._async_create_afk_card(pfp_bytes, name, reason, duration)

    def _sync_create_profile_card(
        self, pfp_bytes: bytes, name: str, username: str, user_id: int, bio: str, pfp_count: int, is_sudo: bool
    ) -> bytes:
        return asyncio.run(self._async_create_profile_card(pfp_bytes, name, username, user_id, bio, pfp_count, is_sudo))

    async def _async_create_profile_card(
        self, pfp_bytes: bytes, name: str, username: str, user_id: int, bio: str, pfp_count: int, is_sudo: bool
    ) -> bytes:
        if pfp_bytes:
            pfp_base64 = "data:image/png;base64," + base64.b64encode(pfp_bytes).decode()
        else:
            initial = name[0].upper() if name else "U"
            default_pfp_bytes = self._get_default_pfp(initial)
            pfp_base64 = "data:image/png;base64," + base64.b64encode(default_pfp_bytes).decode()

        sudo_badge_html = ""
        if is_sudo:
            sudo_badge_html = '<span class="sudo-badge">SUDO</span>'

        username_text = f"@{username} | ID: {user_id}" if username else f"ID: {user_id}"
        bio_text = textwrap.fill(bio, width=55) if bio else "Tidak ada bio."

        html_template = """
        <html>
        <head>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;700&display=swap');
                body {{
                    margin: 0;
                    display: inline-block;
                }}
                .container {{
                    font-family: 'Noto Sans', sans-serif;
                    background: #161B22;
                    color: #C9D1D9;
                    padding: 40px;
                }}
                .top-section {{
                    display: flex;
                    align-items: center;
                    padding-bottom: 30px;
                    border-bottom: 2px solid #30363D;
                }}
                .pfp {{
                    width: 200px;
                    height: 200px;
                    border-radius: 50%;
                    object-fit: cover;
                    margin-right: 40px;
                    flex-shrink: 0;
                }}
                .info {{
                    display: flex;
                    flex-direction: column;
                }}
                .name-line {{
                    display: flex;
                    align-items: center;
                    margin-bottom: 10px;
                }}
                .name {{
                    font-size: 48px;
                    font-weight: 700;
                }}
                .sudo-badge {{
                    background-color: #388E3C;
                    color: #FFFFFF;
                    font-size: 20px;
                    font-weight: 700;
                    padding: 5px 10px;
                    border-radius: 5px;
                    margin-left: 15px;
                }}
                .user-info {{
                    font-size: 32px;
                    color: #8B949E;
                }}
                .bottom-section {{
                    padding-top: 30px;
                }}
                .bio {{
                    font-size: 28px;
                    font-style: italic;
                    margin-bottom: 30px;
                }}
                .stats {{
                    font-size: 24px;
                    color: #8B949E;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="top-section">
                    <img src="{pfp_base64}" class="pfp" />
                    <div class="info">
                        <div class="name-line">
                            <div class="name">{name}</div>
                            {sudo_badge_html}
                        </div>
                        <div class="user-info">{username_text}</div>
                    </div>
                </div>
                <div class="bottom-section">
                    <div class="bio">{bio_text}</div>
                    <div class="stats">Total Foto Profil: {pfp_count}</div>
                </div>
            </div>
        </body>
        </html>
        """.format(
            pfp_base64=pfp_base64,
            name=name,
            sudo_badge_html=sudo_badge_html,
            username_text=username_text,
            bio_text=bio_text,
            pfp_count=pfp_count,
        )

        return await self._render_html_with_playwright(html_content=html_template, selector=".container")

    async def create_profile_card(
        self, pfp_bytes: bytes, name: str, username: str, user_id: int, bio: str, pfp_count: int, is_sudo: bool
    ) -> bytes:
        return await self._async_create_profile_card(pfp_bytes, name, username, user_id, bio, pfp_count, is_sudo)

    def _sync_create_text_sticker(self, text: str) -> bytes:
        clean_text = BeautifulSoup(text, "html.parser").get_text()
        font = self._get_font_from_package("NotoSans-Bold.ttf", 90)

        dummy_img = Image.new("RGBA", (1, 1))
        dummy_draw = ImageDraw.Draw(dummy_img)

        bbox = dummy_draw.textbbox((0, 0), clean_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        padding = 30
        canvas_width = text_width + (padding * 2)
        canvas_height = text_height + (padding * 2)

        canvas = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)

        shadow_color = (0, 0, 0, 100)
        text_color = (255, 255, 255)

        draw.text((padding + 3, padding + 3), clean_text, font=font, fill=shadow_color)
        draw.text((padding, padding), clean_text, font=font, fill=text_color)

        if canvas.width > canvas.height:
            if canvas.width > 512:
                canvas.thumbnail((512, 512), Image.Resampling.LANCZOS)
        else:
            if canvas.height > 512:
                canvas.thumbnail((512, 512), Image.Resampling.LANCZOS)

        output_buffer = BytesIO()
        canvas.save(output_buffer, format="WEBP")
        return output_buffer.getvalue()

    async def create_text_sticker(self, text: str) -> bytes:
        return await self._run_in_executor(self._sync_create_text_sticker, text)

    def _invert_colors_sync(self, image_bytes: bytes) -> bytes:
        with Image.open(BytesIO(image_bytes)) as img:
            inverted_img = ImageOps.invert(img.convert("RGB"))
            output = BytesIO()
            inverted_img.save(output, format="PNG")
            return output.getvalue()

    async def invert_colors(self, image_bytes: bytes) -> bytes:
        return await self._run_in_executor(self._invert_colors_sync, image_bytes)

    def _to_grayscale_sync(self, image_bytes: bytes) -> bytes:
        with Image.open(BytesIO(image_bytes)) as img:
            grayscale_img = ImageOps.grayscale(img)
            output = BytesIO()
            grayscale_img.save(output, format="PNG")
            return output.getvalue()

    async def to_grayscale(self, image_bytes: bytes) -> bytes:
        return await self._run_in_executor(self._to_grayscale_sync, image_bytes)

    def _rotate_image_sync(self, image_bytes: bytes, angle: int) -> bytes:
        with Image.open(BytesIO(image_bytes)).convert("RGBA") as img:
            rotated_img = img.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
            output = BytesIO()
            rotated_img.save(output, format="PNG")
            return output.getvalue()

    async def rotate_image(self, image_bytes: bytes, angle: int) -> bytes:
        return await self._run_in_executor(self._rotate_image_sync, image_bytes, angle)

    def _mirror_image_sync(self, image_bytes: bytes) -> bytes:
        with Image.open(BytesIO(image_bytes)) as img:
            mirrored_img = ImageOps.mirror(img)
            output = BytesIO()
            mirrored_img.save(output, format="PNG")
            return output.getvalue()

    async def mirror_image(self, image_bytes: bytes) -> bytes:
        return await self._run_in_executor(self._mirror_image_sync, image_bytes)

    def _blur_image_sync(self, image_bytes: bytes, radius: int) -> bytes:
        with Image.open(BytesIO(image_bytes)) as img:
            blurred_img = img.filter(ImageFilter.GaussianBlur(radius=radius))
            output = BytesIO()
            blurred_img.save(output, format="PNG")
            return output.getvalue()

    async def blur_image(self, image_bytes: bytes, radius: int) -> bytes:
        return await self._run_in_executor(self._blur_image_sync, image_bytes, radius)

    def _sharpen_image_sync(self, image_bytes: bytes, factor: int) -> bytes:
        with Image.open(BytesIO(image_bytes)) as img:
            sharpened_img = img
            for _ in range(factor):
                sharpened_img = sharpened_img.filter(ImageFilter.SHARPEN)
            output = BytesIO()
            sharpened_img.save(output, format="PNG")
            return output.getvalue()

    async def sharpen_image(self, image_bytes: bytes, factor: int) -> bytes:
        return await self._run_in_executor(self._sharpen_image_sync, image_bytes, factor)
