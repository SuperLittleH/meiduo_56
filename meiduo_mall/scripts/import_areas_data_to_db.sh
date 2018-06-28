#!/bin/bash
mysql -uroot -pmysql meiduo_mall2 < ./areas.sql
mysql -uroot -pmysql meiduo_all2 < goods_data.sql