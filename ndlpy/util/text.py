def render_liquid(data, template, **kwargs):
    """
    Wrapper to liquid renderer.

    :param data: The data to be rendered.
    :type data: dict
    :param template: The template to be rendered.
    :type template: str
    :return: The rendered template.
    :rtype: str
    """
    return data.liquid_to_value(template)
