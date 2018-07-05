import xadmin
from xadmin import views

from . import models


class BaseSetting(object):
    """
    xadmin的基本配置
    """
    enable_themes = True #开启主题切换
    use_bootswatch = True

xadmin.site.register(views.BaseAdminView,BaseSetting)


class Globalsettings(object):
    """
    xadmin的全局配置
    """
    site_title = "美多商城运营管理系统"  # 设置站点标题
    site_footer = "美多商城集团有限公司"  # 设置站点的页脚
    menu_style = "accordion"  # 设置菜单折叠

xadmin.site.register(views.CommAdminView,Globalsettings)


class SKUAdmin(object):
    model_icon = 'fa fa-gift'
    list_display = ['id', 'name', 'price', 'stock', 'sales', 'comments']
    search_fields = ['id','name']
    list_filter = ['category']
    list_editable = ['price', 'stock','sales']
    show_detail_fields = ['name']
    show_bookmarks = True
    list_export = ['xls','csv','xml']
    readonly_fields = ['sales', 'comments']

xadmin.site.register(models.SKU, SKUAdmin)



