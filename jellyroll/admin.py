from django.contrib import admin
from jellyroll.models import Item, Bookmark, Track, Photo, WebSearch, Video
from jellyroll.models import CodeRepository, CodeCommit

class ItemAdmin(admin.ModelAdmin):
    date_hierarchy = 'timestamp'
    list_display = ('timestamp', 'object_str')
    list_filter = ('content_type', 'timestamp')
    search_fields = ('object_str', 'tags')

class BookmarkAdmin(admin.ModelAdmin):
    list_display = ('url', 'description')
    search_fields = ('url', 'description', 'thumbnail')
    
class TrackAdmin(admin.ModelAdmin):
    list_display = ('track_name', 'artist_name')
    search_fields = ('artist_name', 'track_name')

class PhotoAdmin(admin.ModelAdmin):
    list_display = ('title', 'photo_id','description', 'taken_by')
    search_fields = ('title', 'description', 'taken_by')

class WebSearchAdmin(admin.ModelAdmin):
    list_display = ('query',)

class VideoAdmin(admin.ModelAdmin):
    list_display = ('title',)

class CodeRepositoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'type')

class CodeCommitAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'repository')
    list_filter = ('repository',)
    search_fields = ('message',)

admin.site.register(Item, ItemAdmin)
admin.site.register(Bookmark, BookmarkAdmin)
admin.site.register(Track, TrackAdmin)
admin.site.register(Photo, PhotoAdmin)
admin.site.register(WebSearch, WebSearchAdmin)
admin.site.register(Video, VideoAdmin)
admin.site.register(CodeRepository, CodeRepositoryAdmin)
admin.site.register(CodeCommit, CodeCommitAdmin)
