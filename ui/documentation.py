from pathlib import Path
from io import BytesIO
import re
import streamlit as st

# Optional: real Markdown converter
try:
    from markdown import markdown as md_to_html  # pip install markdown
except Exception:
    md_to_html = None

# Optional: image resizing
try:
    from PIL import Image
except Exception:
    Image = None


class StepDocs:
    def __init__(
        self,
        md_path="README.md",
        images_root="images",
        title="Documentation",
        max_width_px=1120,
        img_max_w_px=1080,
        img_max_h_px=520,
    ):
        self.md_path = Path(md_path)
        self.images_root = Path(images_root)
        self.title = title
        self.max_width_px = max_width_px
        self.img_max_w_px = img_max_w_px
        self.img_max_h_px = img_max_h_px

    # ---------- styles ----------
    def _css(self):
        st.markdown(f"""
        <style>
          .block-container {{ max-width: {self.max_width_px}px; padding-top: 1rem !important; }}
          :root {{
            --ui-font: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Inter, "Helvetica Neue", Arial, "Noto Sans", "Liberation Sans", sans-serif;
          }}
          body, .stMarkdown {{ font-family: var(--ui-font) !important; color: #0f172a; line-height:1.65; font-size:16.5px; }}
          h1,h2,h3 {{ letter-spacing:.2px; margin:.25rem 0 .7rem; }}
          h1 {{ font-size:1.8rem; }} h2 {{ font-size:1.35rem; }} h3 {{ font-size:1.1rem; }}

          .step-card {{ border:1px solid #e5e7eb; border-radius:12px; padding:14px 18px; margin:0 0 16px; background:#fff; box-shadow:0 1px 2px rgba(0,0,0,.04); }}
          .step-head {{ display:flex; align-items:center; gap:.6rem; margin-bottom:.25rem; }}
          .step-num {{ width:28px; height:28px; border-radius:7px; display:flex; align-items:center; justify-content:center; background:#4F46E5; color:#fff; font-weight:700; font-size:.95rem; }}
          .step-title {{ font-weight:700; }}

          /* Instruction block */
          .inst {{ background:#f8fafc; border:1px solid #eef2f7; border-radius:10px; padding:12px 14px; margin:.6rem 0 .8rem; }}
          .inst p, .inst li {{ margin:.15rem 0; }}
          .inst blockquote {{ border-left:4px solid #4F46E5; background:#eef2ff; padding:.55rem .8rem; border-radius:8px; }}
          .inst code, .inst pre {{ background:#0f172a10; border-radius:6px; padding:0 .3rem; }}
          .inst a {{ color:#1d4ed8; text-decoration:underline; }}

          /* Image card */
          .img-wrap {{ background:#fff; border:1px solid #e5e7eb; border-radius:10px; padding:8px; margin:.5rem 0 .9rem; box-shadow:0 1px 2px rgba(0,0,0,.03); }}
          .img-label {{ font-size:13px; color:#475569; margin:2px 0 6px 2px; font-weight:600; letter-spacing:.2px; }}
          .stImage img {{ border-radius:8px; border:1px solid #e5e7eb; }}

          /* Sidebar ToC */
          .toc {{ position: sticky; top: 68px; }}
          .toc h4 {{ margin:.25rem 0 .5rem; }}
          .toc a {{ color:#334155; text-decoration:none; display:block; padding:.22rem 0; }}
          .toc a:hover {{ color:#111827; }}
        </style>
        """, unsafe_allow_html=True)

    # ---------- utils ----------
    @staticmethod
    def _slugify(text: str) -> str:
        return re.sub(r'[^a-z0-9\- ]', '', text.lower()).strip().replace(' ', '-')

    @staticmethod
    def _is_step_h2(line: str) -> bool:
        return line.strip().lower().startswith("## step ")

    def _split_steps(self, md_text: str):
        lines = md_text.splitlines()
        steps, cur_title, cur_buf = [], None, []

        def flush():
            if cur_title is not None:
                steps.append((cur_title, "\n".join(cur_buf).strip()))

        for ln in lines:
            if ln.startswith("## "):
                if self._is_step_h2(ln):
                    flush()
                    cur_title = ln.lstrip("# ").strip()
                    cur_buf = []
                else:
                    cur_buf.append(ln)
            else:
                if cur_title is None:
                    continue
                cur_buf.append(ln)
        flush()
        return steps

    # ---------- images ----------
    def _resolve_image_path(self, src: str) -> Path | None:
        p = Path(src)
        if p.is_file(): return p
        p2 = Path(".") / src
        if p2.is_file(): return p2
        p3 = self.images_root / "media" / Path(src).name
        return p3 if p3.is_file() else None

    def _thumbnail_bytes(self, path: Path) -> bytes | None:
        if Image is None: return None
        try:
            with Image.open(path) as im:
                im = im.convert("RGB")
                im.thumbnail((self.img_max_w_px, self.img_max_h_px))
                buf = BytesIO()
                im.save(buf, format="JPEG", quality=92)
                return buf.getvalue()
        except Exception:
            return None

    # ---------- markdown -> html helpers for instruction blocks ----------
    _link_md = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')                 # [text](url)
    _autolink = re.compile(r'(?<!["\'])\bhttps?://[^\s<)]+')          # bare URLs

    def _md_to_html_safe(self, text: str) -> str:
        """Prefer real markdown converter; otherwise minimal conversion (links, line breaks, lists)."""
        if md_to_html:
            html = md_to_html(text, extensions=["extra", "sane_lists", "nl2br"])
        else:
            # minimal: links + preserve paragraphs/line breaks
            html = text
            html = self._link_md.sub(r'<a href="\2">\1</a>', html)
            html = self._autolink.sub(lambda m: f'<a href="{m.group(0)}">{m.group(0)}</a>', html)
            # paragraphs
            parts = [f"<p>{p}</p>" for p in html.split("\n\n") if p.strip()]
            html = "\n".join(parts) if parts else ""
        # open links in new tab
        html = re.sub(r'<a href="', '<a target="_blank" rel="noopener noreferrer" href="', html)
        return html

    # ---------- rendering ----------
    def _render_instruction_block(self, chunk: str):
        """Render instruction text with proper Markdown → HTML, inside the .inst box."""
        # detect HR-only blocks and render as separator
        lines = [ln.strip() for ln in chunk.strip().splitlines() if ln.strip()]
        if not lines:
            return
        if all(ln in ("---", "<hr>", "<hr/>") or re.fullmatch(r"-{3,}", ln) for ln in lines):
            st.markdown("<hr/>", unsafe_allow_html=True)
            return

        html = self._md_to_html_safe(chunk)
        st.markdown(f'<div class="inst">{html}</div>', unsafe_allow_html=True)

    def _render_segment(self, segment_md: str):
        """Render text and images in order; text uses HTML so links always work."""
        img_pattern = re.compile(r'!\[(.*?)\]\((.*?)\)')
        pos = 0
        for m in img_pattern.finditer(segment_md):
            pre = segment_md[pos:m.start()]
            if pre:
                self._render_instruction_block(pre)

            alt, src = m.group(1), m.group(2)
            img_path = self._resolve_image_path(src)

            st.markdown('<div class="img-wrap">', unsafe_allow_html=True)
            if alt:
                st.markdown(f'<div class="img-label">Figure: {alt}</div>', unsafe_allow_html=True)

            if img_path:
                data = self._thumbnail_bytes(img_path) if Image else None
                if data:
                    st.image(data, use_container_width=False, output_format="JPEG")
                else:
                    st.image(str(img_path), use_container_width=True)
            else:
                st.markdown(f"*Image not found:* `{src}`")
            st.markdown('</div>', unsafe_allow_html=True)

            pos = m.end()

        tail = segment_md[pos:]
        if tail:
            self._render_instruction_block(tail)

    def _build_sidebar_toc(self, steps):
        with st.sidebar:
            st.markdown('<div class="toc">', unsafe_allow_html=True)
            st.markdown("### Progress")
            for i, (title, _) in enumerate(steps, start=1):
                anchor = self._slugify(title)
                label = title.split(":", 1)[-1].strip()
                st.markdown(f'- <a href="#{anchor}">{i}. {label}</a>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # ---------- main ----------
    def render(self):
        # st.set_page_config(page_title=self.title, layout="wide")
        self._css()

        if not self.md_path.is_file():
            st.error(f"README not found at: {self.md_path.resolve()}")
            return

        md = self.md_path.read_text(encoding="utf-8")
        steps = self._split_steps(md)

        st.subheader("Mindgenome — Step-by-Step Tutorial")

        if not steps:
            st.warning("No steps found. Use headings like `## Step 1: ...` in your README.")
            self._render_segment(md)
            return

        self._build_sidebar_toc(steps)

        for idx, (title, body) in enumerate(steps, start=1):
            anchor = self._slugify(title)
            label = title.split(":", 1)[-1].strip()
            st.markdown(f'<a id="{anchor}"></a>', unsafe_allow_html=True)
            st.markdown('<div class="step-card">', unsafe_allow_html=True)
            st.markdown(
                f'''
                <div class="step-head">
                  <div class="step-num">{idx}</div>
                  <div class="step-title">{label}</div>
                </div>
                ''',
                unsafe_allow_html=True
            )
            self._render_segment(body)
            st.markdown('</div>', unsafe_allow_html=True)

        st.caption("Links inside instruction boxes now render/behave correctly (open in new tabs).")


# # ---- run page ----
# StepDocs(
#     md_path="README.md",
#     images_root="images",
#     title="Documentation",
#     img_max_w_px=1080,
#     img_max_h_px=520,
# ).render()
