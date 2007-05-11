from django.template import loader
from jellyroll.models import Item

def recent(request, num=30, template_name=None, template_loader=loader,
    extra_context=None, context_processors=None, mimetype=None):
    """
    Recent Jellyroll'd items. 
    
    Works a bit like a generic view in that you can pass a bunch of optional
    keyword arguments:

    * ``num`` -- Number of recent items, default 30.
    
    * ``template_name``, ``template_loader``, ``extra_context``,
      ``context_processors``, ``mimetype`` -- As for generic views.

    Templates: ``jellyroll/calendar/recent.html`` (default)
    Context:
        ``items``
            ``num`` recent items, most recent first.
    """
    pass

def year(request, year, template_name=None, template_loader=loader,
    extra_context=None, context_processors=None, mimetype=None):
    """
    Jellyroll'd items for a particular year.

    Works a bit like a generic view in that you can pass a bunch of optional
    keyword arguments which work just like they do in generic views. Those
    arguments are: ``template_name``, ``template_loader``, ``extra_context``,
    ``context_processors``, and ``mimetype``.

    Templates: ``jellyroll/calendar/year.html`` (default)
    Context:
        ``items``
            Items from the year, earliest first.
        ``year``
            The year.
    """
    pass

def month(request, year, month, template_name=None, template_loader=loader,
    extra_context=None, context_processors=None, mimetype=None):
    """
    Jellyroll'd items for a particular month.

    Works a bit like a generic view in that you can pass a bunch of optional
    keyword arguments which work just like they do in generic views. Those
    arguments are: ``template_name``, ``template_loader``, ``extra_context``,
    ``context_processors``, and ``mimetype``.

    Templates: ``jellyroll/calendar/month.html`` (default)
    Context:
        ``items``
            Items from the month, earliest first.
        ``month``
            The month (a ``datetime.date`` object).
    """
    pass
        
def day(request, year, month, day, template_name=None, template_loader=loader,
    extra_context=None, context_processors=None, mimetype=None):
    """
    Jellyroll'd items for a particular day.

    Works a bit like a generic view in that you can pass a bunch of optional
    keyword arguments which work just like they do in generic views. Those
    arguments are: ``template_name``, ``template_loader``, ``extra_context``,
    ``context_processors``, and ``mimetype``.

    Templates: ``jellyroll/calendar/day.html`` (default)
    Context:
        ``items``
            Items from the month, earliest first.
        ``day``
            The day (a ``datetime.date`` object).
    """
    pass
