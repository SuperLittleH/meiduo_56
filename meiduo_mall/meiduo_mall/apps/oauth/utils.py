from urllib.parse import urlencode,parse_qs
from urllib.request import urlopen
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer,BadData
from django.conf import settings
import json
import logging

from oauth.exceptions import QQAPIError

logger = logging.getLogger('django')

class OAuthQQ(object):
    """
    QQ登录辅助工具类
    """
    def __init__(self,client_id=None,client_secret=None,redirect_uri=None,state=None):
        self.client_id= client_id or settings.QQ_CLIENT_ID
        self.client_secret = client_secret or settings.QQ_CLIENT_SECRET
        self.redirect_uri = redirect_uri or settings.QQ_REDIRECT_URI
        self.state = state or settings.QQ_STATE

    def get_qq_login_url(self):
        """
        获取qq登录的网址
        :return: url网址
        """
        url = 'https://graph.qq.com/oauth2.0/authorize?'
        params = {
            'response_type':'code',
            'client_id':self.client_id,
            'redirect_uri':self.redirect_uri,
            'state':self.state,
            'scope':'get_user_info',
        }
        url += urlencode(params)
        return url

    def get_access_token(self,code):
        """
        获取access_token
        :param code:
        :return:
        """
        params = {
            'grant_type':'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': self.redirect_uri
        }
        url = 'https://graph.qq.com/oauth2.0/token?' + urlencode(params)
        response = urlopen(url)
        response_data = response.read().decode()
        data = parse_qs(response_data)
        access_token = data.get('access_token',None)
        if not access_token:
            logger.error('code=%s msg=%s' % (data.get('code'), data.get('msg')))
            raise QQAPIError

        return access_token[0]


    def get_openid(self,access_token):
        """
        获取用户的openid
        """
        url = 'https://graph.qq.com/oauth2.0/me?access_token=' + access_token
        response = urlopen(url)
        response_data = response.read().decode()
        try:
            # 返回的数据 callback( {"client_id":"YOUR_APPID","openid":"YOUR_OPENID"} )\n;
            data = json.loads(response_data[10:-4])
        except Exception:
            data = parse_qs(response_data)
            logger.error('code=%s msg=%s' % (data.get('code'),data.get('msg')))
            raise QQAPIError
        openid =  data.get('openid',None)
        return openid

    @staticmethod
    def generate_save_user_token(openid):
        """
        生成保存用户数据的token
        :param openid: 用户的openid
        :return: token
        """