import os
import ndlpy
import liquid as liq  # More descriptive alias

def load_template_env(ext=".md", template_dir=None):
    """
    Load in the templates to be used for lists.

    :param ext: The extension of the templates to be loaded, default is Markdown.
    :type ext: str
    :param template_dir: Optional custom directory for templates.
    :type template_dir: str or None
    :return: The template environment.
    :rtype: liquid.Environment
    """
    if template_dir is None:
        template_dir = os.path.join(os.path.dirname(ndlpy.__file__), "templates")

    template_path = [template_dir]
    try:
        env = liq.Environment(loader=liq.loaders.FileExtensionLoader(search_path=template_path, ext=ext))
        return env
    except Exception as e:
        # Handle specific exceptions as needed
        raise RuntimeError(f"Failed to load template environment: {e}")
