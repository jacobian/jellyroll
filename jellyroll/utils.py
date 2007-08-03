try:
    import pygments
    import pygments.lexers
    import pygments.formatters
except ImportError:
    pygments = None
    
def highlight_code(code, language="guess", cssclass="highlight"):
    if pygments is None:
        return "<div class='%s %s'><pre>%s</pre></div>" % (cssclass, language, code)
    if language == "guess":
        try:
            lexer = pygments.lexers.guess_lexer(code)
        except pygments.lexers.ClassNotFound:
            lexer = pygments.lexers.get_lexer_by_name("text")
    else:
        try:
            lexer = pygments.lexers.get_lexer_by_name(language)
        except pygments.lexers.ClassNotFound:
            lexer = pygments.lexers.get_lexer_by_name("text")
            
    return pygments.highlight(code, lexer, pygments.formatters.HtmlFormatter(cssclass=cssclass))
    