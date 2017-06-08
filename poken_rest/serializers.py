# encoding=utf8
import random

from django.contrib.auth.models import User, Group
from rest_framework import serializers

from poken_rest.models import Product, UserLocation, Customer, Seller, ProductBrand, ProductCategory, \
    ProductImage, ProductSize, FeaturedItem, HomeItem, HomeProductSection, ShoppingCart, AddressBook, Location, \
    Shipping, OrderDetails, OrderedProduct

from django.contrib.auth import get_user_model  # If used custom user model

UserModel = get_user_model()


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password',)
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = super(UserSerializer, self).create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ('name',)


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductBrand
        fields = ('name', 'logo')


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ('name',)


class ProductBrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductBrand
        fields = ('name', 'logo')


class ProductSellerSerializer(serializers.ModelSerializer):
    location = serializers.SlugRelatedField(many=False, read_only=True, slug_field='city')

    class Meta:
        model = Seller
        fields = ('id', 'store_name', 'tag_line', 'phone_number', 'location')


class ProductImagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('path',)


class ProductSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSize
        fields = ('name',)


class ProductSerializer(serializers.ModelSerializer):
    seller = ProductSellerSerializer(many=False, read_only=True)
    brand = ProductBrandSerializer(many=False, read_only=True)
    # Show certain field on related relationship
    # ref: http://www.django-rest-framework.org/api-guide/relations/#slugrelatedfield
    category = serializers.SlugRelatedField(many=False, read_only=True, slug_field='name')
    size = serializers.SlugRelatedField(many=False, read_only=True, slug_field='name')
    images = ProductImagesSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'name', 'description', 'seller', 'is_cod', 'is_new', 'date_created', 'brand', 'category',
                  'images', 'size', 'stock', 'price', 'weight')


class ProductCartSerializer(serializers.ModelSerializer):
    # Show certain field on related relationship
    # ref: http://www.django-rest-framework.org/api-guide/relations/#slugrelatedfield
    size = serializers.SlugRelatedField(many=False, read_only=True, slug_field='name')
    images = ProductImagesSerializer(many=True, read_only=True)
    seller = ProductSellerSerializer(many=False, read_only=True)

    class Meta:
        model = Product
        fields = ('name', 'images', 'size', 'stock', 'price', 'weight', 'seller')


class InsertProductSerializer(serializers.ModelSerializer):
    seller = serializers.PrimaryKeyRelatedField(many=False, read_only=False, queryset=Seller.objects.all())
    brand = serializers.PrimaryKeyRelatedField(many=False, read_only=False, queryset=ProductBrand.objects.all())
    category = serializers.PrimaryKeyRelatedField(many=False, read_only=False, queryset=ProductCategory.objects.all())
    size = serializers.PrimaryKeyRelatedField(many=False, read_only=False, queryset=ProductSize.objects.all())
    images = serializers.PrimaryKeyRelatedField(many=True, read_only=False, queryset=ProductImage.objects.all())

    class Meta:
        model = Product
        fields = ('name', 'description', 'seller', 'is_new', 'date_created', 'brand', 'category',
                  'images', 'size', 'stock', 'price', 'weight')


class UserLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLocation
        fields = ('address', 'city', 'district', 'zip', 'state')


class CustomersSerializer(serializers.ModelSerializer):
    related_user = UserSerializer(many=False, read_only=False)
    location = UserLocationSerializer(many=False, read_only=False)

    class Meta:
        model = Customer
        fields = ('id', 'related_user', 'phone_number', 'location')

    def create(self, validated_data):
        user_data = validated_data.pop('related_user')  # Add Django User data
        address_data = validated_data.pop('location')
        user = get_user_model().objects.create_user(**user_data)

        print "User data %s: " % user_data
        print "Django User created %s: " % user
        print "Location data %s: " % address_data

        location_data = UserLocation.objects.create(**address_data)
        customer = Customer.objects.create(related_user=user, location=location_data, **validated_data)

        return customer


class SellerSerializer(serializers.ModelSerializer):
    location = UserLocationSerializer(many=False, read_only=True)
    related_user = UserSerializer(many=False, read_only=True)

    class Meta:
        model = Seller
        fields = ('store_name', 'related_user', 'bio', 'tag_line', 'phone_number', 'location')

    def create(self, validated_data):
        address_data = validated_data.pop('location')
        location_data = UserLocation.objects.create(**address_data)
        customer = Customer.objects.create(location=location_data, **validated_data)

        return customer


class FeaturedItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeaturedItem
        fields = ('name', 'image', 'expiry_date', 'target_id')


class HomeProductSectionSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)
    top_sellers = ProductSellerSerializer(many=True, read_only=True)

    class Meta:
        model = HomeProductSection
        fields = ('name', 'section_action_value', 'section_action_id', 'products', 'top_sellers')


class HomeContentSerializer(serializers.ModelSerializer):
    featured_items = FeaturedItemSerializer(many=True, read_only=True)
    sections = HomeProductSectionSerializer(many=True, read_only=True)

    class Meta:
        model = HomeItem
        fields = ('id', 'featured_items', 'sections',)


class ShoppingCartSerializer(serializers.ModelSerializer):
    product = ProductCartSerializer(many=False)

    class Meta:
        model = ShoppingCart
        fields = ('id', 'product', 'date', 'quantity')


class InsertShoppingCartSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(many=False, read_only=False, queryset=Product.objects.all())

    class Meta:
        model = ShoppingCart
        fields = ('product', 'quantity')

    def create(self, validated_data):
        product_data = validated_data.pop('product')
        quantity_data = validated_data.pop('quantity')

        print "Self data: %s" % dir(self)
        cust = Customer.objects.filter()

        print "Product data: %s" % product_data
        print "Quantity data: %s" % quantity_data

        new_cart = ShoppingCart.objects.create(product=product_data, quantity=quantity_data)

        return new_cart


class AddressBookSerializer(serializers.ModelSerializer):
    customer = serializers.PrimaryKeyRelatedField(many=False, read_only=False, queryset=Customer.objects.all())
    location = UserLocationSerializer(many=False, read_only=False)

    class Meta:
        model = AddressBook
        fields = ('id', 'customer', 'location', 'name', 'address', 'phone')

    def create(self, validated_data):
        cust = validated_data.pop('customer')  # POP remove related field from  validated_data
        location = validated_data.pop('location')

        # name = validated_data.pop('name')
        # address = validated_data.pop('address')
        # phone = validated_data.pop('phone')

        print "Validated data: %s " % validated_data
        print "Cust from validated_data: %s " % cust
        print "Location from validated_data: %s " % location

        created_location = Location.objects.create(**location)

        created_address_book = AddressBook.objects.create(customer=cust, location=created_location, **validated_data)
        return created_address_book


class ShippingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipping
        fields = ('name', 'fee',)


class OrderDetailsSerializer(serializers.ModelSerializer):
    customer = serializers.PrimaryKeyRelatedField(many=False, read_only=False, queryset=Customer.objects.all())
    address = AddressBookSerializer(many=False, read_only=False)
    shipping = ShippingSerializer(many=False, read_only=False)

    class Meta:
        model = OrderDetails
        fields = ('id', 'customer', 'address', 'date', 'shipping')


class OrderedProductSerializer(serializers.ModelSerializer):
    order_details = OrderDetailsSerializer(many=False, read_only=True)
    shopping_cart = ShoppingCartSerializer(many=True, read_only=True)

    class Meta:
        model = OrderedProduct
        fields = ('id', 'order_details', 'shopping_cart', 'status')