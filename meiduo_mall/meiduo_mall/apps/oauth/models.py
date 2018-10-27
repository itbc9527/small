from django.db import models

# Create your models here.


class OauthQQUser(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name='qq用户')
    openid = models.CharField(max_length=64, verbose_name='openid', db_index=True)

    class Meta:
        db_table = 'tb_oauth_qq'
        verbose_name = 'QQ用户登陆数据'
        verbose_name_plural = 'QQ用户登陆数据'
