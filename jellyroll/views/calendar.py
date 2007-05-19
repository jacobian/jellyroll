"""
Views for looking at Jellyroll items by date.

These act as kinda-sorta generic views in that they take a number of the same
arguments as generic views do (i.e. ``template_name``, ``extra_context``, etc.)

They all also take an argument ``queryset`` which should be an ``Item``
queryset; it'll be used as the *starting point* for the the view in question
instead of ``Item.objects.all()``.
"""

import time
import datetime
from django.core import urlresolvers
from django.template import loader, RequestContext
from django.http import Http404, HttpResponse
from jellyroll.models import Item

def today(request, **kwargs):
    """
    Jellyroll'd items today
    
    See :view:`jellyroll.views.calendar.day`
    """
    y, m, d = datetime.date.today().strftime("%Y/%b/%d").lower().split("/")
    if "template_name" not in kwargs:
        kwargs['template_name'] = "jellyroll/calendar/today.html"
    return day(request, y, m, d, recent_first=True, **kwargs)

def year(request, year, queryset=None,
    template_name="jellyroll/calendar/year.html", template_loader=loader,
    extra_context=None, context_processors=None, mimetype=None):
    """
    Jellyroll'd items for a particular year.

    Works a bit like a generic view in that you can pass a bunch of optional
    keyword arguments which work just like they do in generic views. Those
    arguments are: ``template_name``, ``template_loader``, ``extra_context``,
    ``context_processors``, and ``mimetype``.
    
    You can also pass a ``queryset`` argument; see the module's docstring
    for information about how that works.

    Templates: ``jellyroll/calendar/year.html`` (default)
    Context:
        ``items``
            Items from the year, earliest first.
        ``year``
            The year.
        ``previous``
            The previous year; ``None`` if that year was before jellyrolling
            started..
        ``previous_link``
            Link to the previous year
        ``next``
            The next year; ``None`` if it's in the future.
        ``next_year``
            Link to the next year
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
    previous = year - 1
    previous_link = urlresolvers.reverse("jellyroll.views.calendar.year", args=[previous])
    if previous < first.timestamp.year:
        previous = previous_link = None
    
    # And the next year
    next = year + 1
    next_link = urlresolvers.reverse("jellyroll.views.calendar.year", args=[next])
    if next > today.year:
        next = next_link = None
        
    # Handle the initial queryset
    if not queryset:
        queryset = Item.objects.all()
    queryset = queryset.filter(timestamp__year=year)
    if queryset._order_by is None:
        queryset = queryset.order_by("timestamp")
        
    # Build the context
    context = RequestContext(request, {
        "items"         : queryset.filter(timestamp__year=year).order_by("timestamp"),
        "year"          : year,
        "previous"      : previous,
        "previous_link" : previous_link,
        "next"          : next,
        "next_link"     : next_link
    }, context_processors)
    if extra_context:
        for key, value in extra_context.items():
            if callable(value):
                context[key] = value()
            else:
                context[key] = value
    
    # Load, render, and return
    t = template_loader.get_template(template_name)
    return HttpResponse(t.render(context), mimetype=mimetype)

def month(request, year, month, queryset=None,
    template_name="jellyroll/calendar/month.html", template_loader=loader,
    extra_context=None, context_processors=None, mimetype=None):
    """
    Jellyroll'd items for a particular month.

    Works a bit like a generic view in that you can pass a bunch of optional
    keyword arguments which work just like they do in generic views. Those
    arguments are: ``template_name``, ``template_loader``, ``extra_context``,
    ``context_processors``, and ``mimetype``.
    
    You can also pass a ``queryset`` argument; see the module's docstring
    for information about how that works.

    Templates: ``jellyroll/calendar/month.html`` (default)
    Context:
        ``items``
            Items from the month, earliest first.
        ``month``
            The month (a ``datetime.date`` object).
        ``previous``
            The previous month; ``None`` if that month was before jellyrolling
            started.
        ``previous_link``
            Link to the previous month
        ``next``
            The next month; ``None`` if it's in the future.
        ``next_link``
            Link to the next month
    """
    # Make sure we've requested a valid month
    try:
        date = datetime.date(*time.strptime(year+month, '%Y%b')[:3])
    except ValueError:
        raise Http404("Invalid month string")
    try:
        first = Item.objects.order_by("timestamp")[0]
    except IndexError:
        raise Http404("No items; no views.")
    
    # Calculate first and last day of month, for use in a date-range lookup.
    today = datetime.date.today()
    first_day = date.replace(day=1)
    if first_day.month == 12:
        last_day = first_day.replace(year=first_day.year + 1, month=1)
    else:
        last_day = first_day.replace(month=first_day.month + 1)
    
    if first_day < first.timestamp.date().replace(day=1) or date > today:
        raise Http404("Invalid month (%s .. %s)" % (first.timestamp.date(), today))
    
    # Calculate the previous month
    previous = (first_day - datetime.timedelta(days=1)).replace(day=1)
    previous_link = urlresolvers.reverse("jellyroll.views.calendar.month", args=previous.strftime("%Y %b").lower().split())
    if previous < first.timestamp.date().replace(day=1):
        previous = None
    
    # And the next month
    next = last_day + datetime.timedelta(days=1)
    next_link = urlresolvers.reverse("jellyroll.views.calendar.month", args=next.strftime("%Y %b").lower().split())
    if next > today:
        next = None
        
    # Handle the initial queryset
    if not queryset:
        queryset = Item.objects.all()
    queryset = queryset.filter(timestamp__range=(first_day, last_day))
    if queryset._order_by is None:
        queryset = queryset.order_by("timestamp")
    
    # Build the context
    context = RequestContext(request, {
        "items"         : queryset,
        "month"         : date,
        "previous"      : previous,
        "previous_link" : previous_link,
        "next"          : next,
        "next_link"     : next_link
    }, context_processors)
    if extra_context:
        for key, value in extra_context.items():
            if callable(value):
                context[key] = value()
            else:
                context[key] = value
    
    # Load, render, and return
    t = template_loader.get_template(template_name)
    return HttpResponse(t.render(context), mimetype=mimetype)
        
def day(request, year, month, day, queryset=None, recent_first=False,
    template_name="jellyroll/calendar/day.html", template_loader=loader,
    extra_context=None, context_processors=None, mimetype=None):
    """
    Jellyroll'd items for a particular day.

    Works a bit like a generic view in that you can pass a bunch of optional
    keyword arguments which work just like they do in generic views. Those
    arguments are: ``template_name``, ``template_loader``, ``extra_context``,
    ``context_processors``, and ``mimetype``.
    
    Also takes a ``recent_first`` param; if it's ``True`` the newest items
    will be displayed first; otherwise items will be ordered earliest first.

    You can also pass a ``queryset`` argument; see the module's docstring
    for information about how that works.

    Templates: ``jellyroll/calendar/day.html`` (default)
    Context:
        ``items``
            Items from the month, ordered according to ``recent_first``.
        ``day``
            The day (a ``datetime.date`` object).
        ``previous``
            The previous day; ``None`` if that day was before jellyrolling
            started.
        ``previous_link``
            Link to the previous day
        ``next``
            The next day; ``None`` if it's in the future.
        ``next_link``
            Link to the next day.
        ``is_today``
            ``True`` if this day is today.
    """
    # Make sure we've requested a valid month
    try:
        day = datetime.date(*time.strptime(year+month+day, '%Y%b%d')[:3])
    except ValueError:
        raise Http404("Invalid day string")
    try:
        first = Item.objects.order_by("timestamp")[0]
    except IndexError:
        raise Http404("No items; no views.")
    
    today = datetime.date.today()
    if day < first.timestamp.date() or day > today:
        raise Http404("Invalid day (%s .. %s)" % (first.timestamp.date(), today))
    
    # Calculate the previous day
    previous = day - datetime.timedelta(days=1)
    previous_link = urlresolvers.reverse("jellyroll.views.calendar.day", args=previous.strftime("%Y %b %d").lower().split())
    if previous < first.timestamp.date():
        previous = previous_link = None
    
    # And the next month
    next = day + datetime.timedelta(days=1)
    next_link = urlresolvers.reverse("jellyroll.views.calendar.day", args=next.strftime("%Y %b %d").lower().split())
    if next > today:
        next = next_link = None
    
    # Some lookup values...
    timestamp_range = (datetime.datetime.combine(day, datetime.time.min), 
                       datetime.datetime.combine(day, datetime.time.max))
    
    # Handle the initial queryset
    if not queryset:
       queryset = Item.objects.all()
    queryset = queryset.filter(timestamp__range=timestamp_range)
    if queryset._order_by is None:
        if recent_first:
            queryset = queryset.order_by("-timestamp")
        else:
            queryset = queryset.order_by("timestamp")
    
    # Build the context
    context = RequestContext(request, {
        "items"         : queryset,
        "day"           : day,
        "previous"      : previous,
        "previous_link" : previous_link,
        "next"          : next,
        "next_link"     : next_link,
        "is_today"      : day == today,
    }, context_processors)
    if extra_context:
        for key, value in extra_context.items():
            if callable(value):
                context[key] = value()
            else:
                context[key] = value
    
    # Load, render, and return
    t = template_loader.get_template(template_name)
    return HttpResponse(t.render(context), mimetype=mimetype)
