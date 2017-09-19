# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import thread
import threading

import requests
from django.utils import html
from django.utils.formats import localize

from poken_psp import properties

URL_SLACK_POKEN_SALES = "https://hooks.slack.com/services/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"
URL_SLACK_POKEN_ORDER_EXPIRE = "https://hooks.slack.com/services/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"

class FuncThread(threading.Thread):
    def __init__(self, target, *args):
        self._target = target
        self._args = args
        threading.Thread.__init__(self)

    def run(self):
        self._target(*self._args)


def send_slack_order_expire_notif(expire_order_detail):

    request = expire_order_detail['request']
    order_details = expire_order_detail['data']

    order_ref = order_details.order_id
    customer = order_details.customer
    cust_name = html.escape(str(customer.related_user.get_full_name()))

    payload = """
    {
    "text": "Pesanan Barang order ref. %s oleh %s telah hangus.",
    }
    """ % (
        order_ref,
        cust_name,
    )

    headers = {
        'content-type': "application/json",
        'cache-control': "no-cache"
    }

    response = requests.request("POST", URL_SLACK_POKEN_ORDER_EXPIRE, data=payload, headers=headers)

    print ("Slack webhook order-expire response: " + str(response.text))


def send_slack_new_order_notif(new_ordered_product):

    request = new_ordered_product['request']
    ordered_product = new_ordered_product['data']

    url_order = request.build_absolute_uri(
        'admin/poken_rest/orderdetails/%d/change/' % ordered_product.order_details.id)

    order_id_link = '<%s|%s>' % (url_order, ordered_product.order_details.order_id)
    order_date = localize(ordered_product.order_details.date)
    customer = ordered_product.order_details.customer
    address_book = ordered_product.order_details.address_book
    cust_name = html.escape(str(customer.related_user.get_full_name()))
    shipping_receiver_name = html.escape(str(address_book.name))
    shipping_receiver_phone = html.escape(address_book.phone)
    shipping_receiver_address = html.escape(address_book.address)

    # Generate ordered product
    str_ordered_temp = """{
            "title": "%s",
			"title_link": "%s",
            "text": "%s",
			"fields": [
                {
                    "title": "Jumlah Pesanan",
                    "value": "%d",
                    "short": true
                },
                {
                    "title": "Stok Barang",
                    "value": "%d",
                    "short": true
                }
            ]        
		}, {
            "title": "Catatan Untuk Penjual",
            "text": "%s",
			"fields": [
                {
                    "title": "Nama Toko",
                    "value": "%s",
                    "short": true
                },
                {
                    "title": "Nomor Telp. Toko",
                    "value": "<tel:%s|%s>",
                    "short": true
                }
            ]
        }"""
    str_ordered_items = ""
    for sc in ordered_product.shopping_carts.all():
        str_ordered_items += str_ordered_temp % (
            html.escape(sc.product.name.replace('"', '\\"')),
            html.escape(request.build_absolute_uri(sc.product.images.first().path.url)),
            html.escape(str(sc.product.description).replace('"', '\\"'))[:100],  # First hundred
            sc.quantity,
            sc.product.stock,
            html.escape(sc.extra_note.replace('"', '\\"')),
            html.escape(sc.product.seller.store_name.replace('"', '\\"')),
            html.escape(sc.product.seller.phone_number), html.escape(sc.product.seller.phone_number)
        ) + ","

    str_ordered_items = str_ordered_items.rsplit(',', 1)[0]

    payload = """
    {
    "text": "Pesanan Barang Baru oleh %s",
    "attachments": [
        {
            "title": "Profile Pembeli",
            "text": "Order ref. %s pada %s",
            "color": "#904799",
			"fields": [
                {
                    "title": "Nama",
                    "value": "%s",
                    "short": true
                },
                {
                    "title": "Nomor Telp. Pembeli",
                    "value": "<tel:%s|%s>",
                    "short": true
                },
                {
                    "title": "Alamat",
                    "value": "%s",
                    "short": true
                }
            ]        
		},
		%s
    ]
    }
    """ % (
        cust_name,
        order_id_link,
        order_date,
        shipping_receiver_name,
        shipping_receiver_phone, shipping_receiver_phone,
        shipping_receiver_address,
        str_ordered_items
    )

    headers = {
        'content-type': "application/json",
        'cache-control': "no-cache"
    }

    response = requests.request("POST", URL_SLACK_POKEN_SALES, data=payload, headers=headers)
    # Send simple version
    if response.text != 'ok':
        payload2 = """
                    {
                    "text": "Pesanan Barang Baru oleh %s",
                    "attachments": [
                        {
                            "title": "Profile Pembeli",
                            "text": "Pemesanan %s pada %s",
                            "color": "#F6902D",
                            "fields": [
                                {
                                    "title": "Nama",
                                    "value": "%s",
                                    "short": true
                                },
                                {
                                    "title": "Nomor Pembeli",
                                    "value": "<tel:%s|%s>",
                                    "short": true
                                },
                                {
                                    "title": "Alamat",
                                    "value": "%s",
                                    "short": true
                                }
                            ]        
                        }
                    ]
                    }
                    """% (
                            cust_name,
                            order_id_link,
                            order_date,
                            shipping_receiver_name,
                            shipping_receiver_phone, shipping_receiver_phone,
                            shipping_receiver_address,
                        )
        requests.request("POST", URL_SLACK_POKEN_SALES, data=payload2, headers=headers)


# NEW ORDER SLACK MESSAGE.
def start_message_ordered_product(new_ordered_product, request):
    slack_content = {
        'request': request,
        'data': new_ordered_product
    }

    if properties.IS_SLACK_MESSAGE_ON:
        thread.start_new_thread(send_slack_new_order_notif, (slack_content,))

def start_message_order_expire(expire_order_detail, request):
    slack_content = {
        'request': request,
        'data': expire_order_detail
    }

    if properties.IS_SLACK_MESSAGE_ON:
        thread.start_new_thread(send_slack_order_expire_notif, (slack_content,))
