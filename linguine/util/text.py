from linguine.util.misc import remove_nan

def render_liquid(compute, template, **kwargs):
    """
    Wrapper to liquid renderer.

    :param template: The template to be rendered.
    :type template: str
    :return: The rendered template.
    :rtype: str
    """
    return compute._liquid_env.from_string(template).render(**remove_nan(kwargs))
