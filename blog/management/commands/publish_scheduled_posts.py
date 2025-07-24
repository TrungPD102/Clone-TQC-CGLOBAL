from django.core.management.base import BaseCommand
from django.utils import timezone
from blog.models import Post

class Command(BaseCommand):
    help = 'Checks for scheduled posts and publishes them if their publish_at time has come.'

    def handle(self, *args, **options):
        now = timezone.now()
        posts_to_publish = Post.objects.filter(
            status=Post.Status.DA_DUYET,
            publish_at__isnull=False,
            publish_at__lte=now # publish_at đã đến hoặc đã qua
        )

        count = 0
        for post in posts_to_publish:
            post.status = Post.Status.DA_XUAT_BAN
            # Bạn có thể muốn cập nhật lại publish_at thành now nếu nó ở quá khứ
            # post.publish_at = now 
            post.save()
            count += 1

        if count > 0:
            self.stdout.write(self.style.SUCCESS(f'Successfully published {count} scheduled post(s).'))
        else:
            self.stdout.write(self.style.SUCCESS('No posts to publish at this time.'))