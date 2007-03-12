import datetime
from django.db import models
from django.db.models import signals
from django.dispatch import dispatcher
from django.contrib.contenttypes.models import ContentType

class ItemManager(models.Manager):
    def create_or_update(self, instance, timestamp=None, tags="", source="INTERACTIVE", source_id=""):
        """
        Create or update an Item from some instace.
        """
        # If the instance hasn't already been saved, save it first. This
        # requires disconnecting the post-save signal that might be sent to
        # this function (otherwise we could get an infinite loop).
        if instance._get_pk_val() is None:
            try:
                dispatcher.disconnect(self.create_or_update, signal=signals.post_save, sender=type(instance))
            except dispatcher.errors.DispatcherError:
                reconnect = False
            else:
                reconnect = True
            instance.save()
            if reconnect:
                dispatcher.connect(self.create_or_update, signal=signals.post_save, sender=type(instance))
        
        # Check to see if the timestamp is being updated.
        if timestamp is None:
            update_timestamp = False
            timestamp = datetime.datetime.now()
        else:
            update_timestamp = True
        
        # Create the Item object.
        ctype = ContentType.objects.get_for_model(instance)
        item, created = self.get_or_create(
            content_type = ctype, 
            object_id = instance._get_pk_val(),
            defaults = dict(
                timestamp = timestamp,
                source = source,
                source_id = source_id,
                tags = tags,
            )
        )        
        item.tags = tags
        item.source = source
        item.source_id = source_id
        if update_timestamp:
            item.timestamp = timestamp
            
        # Save and return the item.
        item.save()
        return item
        
    def follow_model(self, model):
        """
        Follow a particular model class, updating associated Items automatically.
        """
        dispatcher.connect(self.create_or_update, signal=signals.post_save, sender=model)
        
    def get_for_model(self, model):
        """
        Return a QuerySet of only items of a certain type.
        """
        return self.filter(content_type=ContentType.objects.get_for_model(model))
        
    def get_last_update_of_model(self, model, **kwargs):
        """
        Return the last time a given model's items were updated. Returns the
        epoch if the items were never updated.
        """
        qs = self.get_for_model(model)
        if kwargs:
            qs = qs.filter(**kwargs)
        try:
            return qs.order_by('-timestamp')[0].timestamp
        except IndexError:
            return datetime.datetime.fromtimestamp(0)
