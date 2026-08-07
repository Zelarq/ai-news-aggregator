import datetime

# Allowed categories taxonomy
CATEGORIES = ["Model Release", "Research Paper", "Tool/Framework", "Industry News", "Community Discussion"]

# Color mappings for the category pills
CATEGORY_COLORS = {
    "Model Release": {"bg": "#e6fffa", "text": "#047857", "border": "#10b981"},
    "Research Paper": {"bg": "#ebf8ff", "text": "#1d4ed8", "border": "#3b82f6"},
    "Tool/Framework": {"bg": "#fffbeb", "text": "#b45309", "border": "#f59e0b"},
    "Industry News": {"bg": "#fdf2f8", "text": "#be185d", "border": "#ec4899"},
    "Community Discussion": {"bg": "#faf5ff", "text": "#6b21a8", "border": "#8b5cf6"}
}


def group_items_by_category(items):
    """Groups a list of news items by their category."""
    grouped = {}
    for item in items:
        cat = item.get("category", "Industry News")
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append(item)
    return grouped

def build_html_digest(items):
    """
    Assembles a list of summarized items into a responsive, high-aesthetic HTML email template.
    Uses clean inline-CSS compatible with modern email clients.
    """
    grouped_items = group_items_by_category(items)
    
    # Date heading
    date_str = datetime.date.today().strftime("%B %d, %Y")
    
    # CSS Styles for the email
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI News Digest - {date_str}</title>
    </head>
    <body style="margin: 0; padding: 0; background-color: #0f172a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #e2e8f0; -webkit-font-smoothing: antialiased;">
        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #0f172a; padding: 20px 0;">
            <tr>
                <td align="center">
                    <table border="0" cellpadding="0" cellspacing="0" width="600" style="max-width: 600px; background-color: #1e293b; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06); border: 1px solid #334155;">
                        <!-- Header Banner -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%); padding: 35px 24px; text-align: left;">
                                <span style="background-color: rgba(255,255,255,0.15); color: #ffffff; padding: 4px 10px; border-radius: 9999px; font-size: 11px; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase;">DAILY DIGEST</span>
                                <h1 style="margin: 8px 0 0 0; color: #ffffff; font-size: 28px; font-weight: 800; letter-spacing: -0.025em;">AI News Digest</h1>
                                <p style="margin: 6px 0 0 0; color: #e2e8f0; font-size: 14px; opacity: 0.9;">Autonomous daily synthesis of AI research, tools, and releases.</p>
                            </td>
                        </tr>
                        
                        <!-- Date Badge -->
                        <tr>
                            <td style="padding: 16px 24px 0 24px; border-bottom: 1px solid #334155;">
                                <p style="margin: 0 0 12px 0; color: #94a3b8; font-size: 13px; font-weight: 500;">
                                    📅 Prepared on {date_str} • Local Machine Run
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Main Content -->
                        <tr>
                            <td style="padding: 24px;">
    """
    
    if not items:
        html_content += """
                                <div style="text-align: center; padding: 40px 20px;">
                                    <p style="color: #94a3b8; font-size: 16px; margin: 0;">No new AI news items collected in the last 24 hours.</p>
                                    <p style="color: #64748b; font-size: 14px; margin: 8px 0 0 0;">Check back tomorrow!</p>
                                </div>
        """
    else:
        # Loop through categories in a clean order
        for cat in CATEGORIES:
            cat_items = grouped_items.get(cat, [])
            if not cat_items:
                continue
                
            colors = CATEGORY_COLORS.get(cat, {"bg": "#334155", "text": "#ffffff", "border": "#475569"})
            
            # Category Header
            html_content += f"""
                                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="margin-top: 10px; margin-bottom: 16px;">
                                    <tr>
                                        <td style="padding: 10px 0 6px 0;">
                                            <span style="background-color: {colors['bg']}; color: {colors['text']}; border: 1px solid {colors['border']}; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.03em;">
                                                {cat}
                                            </span>
                                        </td>
                                    </tr>
                                </table>
            """
            
            # Render items in this category
            for item in cat_items:
                src = item.get("source")
                if src == "youtube":
                    source_tag = "🔴 YT"
                    source_color = "#ef4444"
                elif src == "hackernews":
                    source_tag = "🟠 HN"
                    source_color = "#f97316"
                else:
                    source_tag = "🧡 RD"
                    source_color = "#ff4500"
                
                html_content += f"""
                                <!-- Article Card -->
                                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #0f172a; border-radius: 8px; margin-bottom: 16px; border: 1px solid #334155; overflow: hidden;">
                                    <tr>
                                        <td style="padding: 16px;">
                                            <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                                <tr>
                                                    <td>
                                                        <span style="color: {source_color}; font-size: 11px; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;">
                                                            {source_tag}
                                                        </span>
                                                        <h3 style="margin: 4px 0 8px 0; font-size: 16px; font-weight: 700; line-height: 1.4; color: #f8fafc;">
                                                            {item.get('title')}
                                                        </h3>
                                                        <p style="margin: 0 0 12px 0; font-size: 13.5px; line-height: 1.5; color: #cbd5e1;">
                                                            {item.get('summary')}
                                                        </p>
                                                        <a href="{item.get('url')}" target="_blank" style="color: #60a5fa; font-size: 12px; font-weight: 600; text-decoration: none; display: inline-block;">
                                                            Read Original Source &rarr;
                                                        </a>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                </table>
                """
                
    # Footer
    html_content += """
                            </td>
                        </tr>
                        
                        <!-- Footer Info -->
                        <tr>
                            <td style="background-color: #0f172a; padding: 24px; text-align: center; border-top: 1px solid #334155;">
                                <p style="margin: 0; color: #64748b; font-size: 12px;">
                                    This digest was built and sent autonomously by your local AI News Agent.<br>
                                    100% Free / Local Inference Runtime via Ollama & SQLite.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    return html_content

def build_plain_text_digest(items):
    """Fallback plain-text version of the digest."""
    date_str = datetime.date.today().strftime("%B %d, %Y")
    grouped_items = group_items_by_category(items)
    
    text = f"=== AI NEWS DIGEST - {date_str} ===\n\n"
    
    if not items:
        text += "No new items collected today.\n"
        return text
        
    for cat in CATEGORIES:
        cat_items = grouped_items.get(cat, [])
        if not cat_items:
            continue
            
        text += f"\n--- {cat.upper()} ---\n"
        for item in cat_items:
            source = "YouTube" if item.get("source") == "youtube" else "Reddit"
            text += f"\n* {item.get('title')} ({source})\n"
            text += f"  Summary: {item.get('summary')}\n"
            text += f"  URL: {item.get('url')}\n"
            
    text += "\n\nGenerated by your local AI News Agent (Zero-Cost Pipeline).\n"
    return text

if __name__ == "__main__":
    # Test composer
    test_items = [
        {
            "title": "Ollama adds support for Llama 3.1 8B tool calling",
            "summary": "Ollama has updated its integration to support native tool calling and function definition parsing inside Llama 3.1. This unlocks structural agent applications locally.",
            "category": "Tool/Framework",
            "source": "youtube",
            "url": "https://youtube.com/watch?v=test1"
        },
        {
            "title": "Discussion on scaling laws: Are LLMs hitting a cognitive wall?",
            "summary": "Reddit users discuss recent claims from labs about diminishing returns in foundational pretraining. The consensus highlights that post-training and test-time compute represent the next scaling frontier.",
            "category": "Community Discussion",
            "source": "reddit",
            "url": "https://reddit.com/comments/test2"
        }
    ]
    html = build_html_digest(test_items)
    print("HTML digest generation check:")
    print(f"Generated HTML size: {len(html)} bytes")
    print("HTML contains first title:", "Ollama adds support" in html)
