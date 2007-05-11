import datetime
from django.template import loader, RequestContext
from django.shortcuts import render_to_response
from django.http import Http404, HttpResponse
from jellyroll.models import Item

def today(request, **kwargs):
    """
    Jellyroll'd items today
    
    See :view:`jellyroll.views.calendar.day`
    """
    return day(recent_first=True, *datetime.date.today().strftime("%Y/%b/%d").split("/"), **kwargs)

def year(request, year, template_name="jellyroll/calendar/year.html",
    template_loader=loader, extra_context=None, context_processors=None,
    mimetype=None):
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
        ``previous``
            The previous year; ``None`` if that year was before jellyrolling
            started..
        ``next``
            The next year; ``None`` if it's in the future.
    """
    # Make sure we've requested a valid year
    year = int(year)
    try:
        first = Item.objects.order_by("timestamp")[0]
    except IndexError:
        raise Http404("No items; no views.")
    today = datetime.date.today()
    if year < first.timestamp.year or year > today.year:
        raise Http404("Invalid year (%s .. %s)" % (first.timestamp.year, today.year))
    
    # Calculate the previous year
    if year > first.timestamp.year:
        previous = year - 1
    else:
        previous = None
    
    # And the next year
    if year < today.year:
        next = year + 1
    else:
        next = None
    
    # Build the context
    context = RequestContext(request, {
        "items"     : Item.objects.filter(timestamp__year=year).order_by("timestamp"),
        "year"      : year,
        "previous"  : previous,
        "next"      : next,
    }, context_processors)
    if extra_context:
        for key, value in extra_context.items():
            if callable(v):
                context[key] = value()
            else:
                context[key] = value
    
    # Load, render, and return
    t = template_loader.get_template(template_name)
    return HttpResponse(t.render(context), mimetype=mimetype)

def month(request, year, month, template_name="jellyroll/calendar/month.html",
    template_loader=loader, extra_context=None, context_processors=None,
    mimetype=None):
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
        ``previous``
            The previous month; ``None`` if that month was before jellyrolling
            started..
        ``next``
            The next month; ``None`` if it's in the future.
    """
    pass
        
def day(request, year, month, day, recent_first=False, template_name=None,
    template_loader=loader, extra_context=None, context_processors=None,
    mimetype=None):
    """
    Jellyroll'd items for a particular day.

    Works a bit like a generic view in that you can pass a bunch of optional
    keyword arguments which work just like they do in generic views. Those
    arguments are: ``template_name``, ``template_loader``, ``extra_context``,
    ``context_processors``, and ``mimetype``.
    
    Also takes a ``recent_first`` param; if it's ``True`` the newest items
    will be displayed first; otherwise items will be ordered earliest first.

    Templates: ``jellyroll/calendar/day.html`` (default)
    Context:
        ``items``
            Items from the month, ordered according to ``recent_first``.
        ``day``
            The day (a ``datetime.date`` object).
        ``previous``
            The previous day; ``None`` if that day was before jellyrolling
            started..
        ``next``
            The next day; ``None`` if it's in the future.
    """
    pass
