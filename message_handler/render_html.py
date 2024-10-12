import re
import markdown
import bleach
import logging
logger = logging.getLogger(__name__)

# https://core.telegram.org/bots/api#html-style
markdown_text='''
*bold \\*text*
_italic \\*text_
__underline__
~strikethrough~
||spoiler||
*bold _italic bold ~italic bold strikethrough ||italic bold strikethrough spoiler||~ __underline italic bold___ bold*
[inline URL](http://www.example.com/)
[inline mention of a user](tg://user?id=123456789)
![👍](tg://emoji?id=5368324170671202286)
`inline fixed-width code`

```
pre-formatted fixed-width code block
```

``` python
pre-formatted fixed-width code block written in the Python programming language
```

```python
pre-formatted fixed-width code block written in the Python programming language
```

>Block quotation started
>Block quotation continued
>Block quotation continued
>Block quotation continued
>The last line of the block quotation
**>The expandable block quotation started right after the previous block quotation
>It is separated from the previous block quotation by an empty bold entity
>Expandable block quotation continued
>Hidden by default part of the expandable block quotation started
>Expandable block quotation continued
>The last line of the expandable block quotation with the expandability mark||
'''

'''
<b>bold</b>, <strong>bold</strong>
<i>italic</i>, <em>italic</em>
<u>underline</u>, <ins>underline</ins>
<s>strikethrough</s>, <strike>strikethrough</strike>, <del>strikethrough</del>
<span class="tg-spoiler">spoiler</span>, <tg-spoiler>spoiler</tg-spoiler>
<b>bold <i>italic bold <s>italic bold strikethrough <span class="tg-spoiler">italic bold strikethrough spoiler</span></s> <u>underline italic bold</u></i> bold</b>
<a href="http://www.example.com/">inline URL</a>
<a href="tg://user?id=123456789">inline mention of a user</a>
<tg-emoji emoji-id="5368324170671202286">👍</tg-emoji>
<code>inline fixed-width code</code>
<pre>pre-formatted fixed-width code block</pre>
<pre><code class="language-python">pre-formatted fixed-width code block written in the Python programming language</code></pre>
<blockquote>Block quotation started\nBlock quotation continued\nThe last line of the block quotation</blockquote>
<blockquote expandable>Expandable block quotation started\nExpandable block quotation continued\nExpandable block quotation continued\nHidden by default part of the block quotation started\nExpandable block quotation continued\nThe last line of the block quotation</blockquote>
'''

allowed_tags = [
  'p', 'br', # will be stripped
  'b', 'strong', 
  'i', 'em', 
  'h1', 'h2', 'h3', 'h4', 'h5', 'h6', # will be replaced with b
  'u', 'ins', 
  's', 'strike', 'del', 
  'span', 'tg-spoiler', 
  'a', 
  'tg-emoji', 
  'code', 'pre'
]

allowed_attributes = {
    'span': ['class'],
    'a': ['href'],
    'tg-emoji': ['emoji-id'],
    'code': ['class']
}

def render(markdown_text: str) -> str:
  markdown_text = re.sub(r'(?m)^(\s*)- ', r'\1&#8226; ', markdown_text)
  markdown_text = re.sub(r'(?m)^(\s*)(\d+)\.\s', r'\1\2\\. ', markdown_text)
  html = markdown.markdown(markdown_text, extensions=['fenced_code', 'nl2br'])
  html = re.sub(r'(?m)<p>', r'\n', html)
  html = re.sub(r'(?m)<\/p>', r'', html)
  html = re.sub(r'(?m)<br />', r'', html)
  html = re.sub(r'(?m)<h\d>(.*?)<\/h\d>', r'<b>\1</b>', html)
  clean_html = bleach.clean(html, tags=allowed_tags, attributes=allowed_attributes)
  return clean_html