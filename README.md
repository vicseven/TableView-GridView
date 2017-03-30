# TableView-GridView
Django TableView &amp; GridView

Version 0.1
NOT STABLE

Installation:
1) Add generic folder to Djando root project folder
2) Add 'generic' to INSTALLED_APPS in setting.py

Example:

Model:
```
class Customer(models.Model):
    name = models.CharField(max_length=50)
    email = models.EmailField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True)
    birthdate = models.DateField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"
        
    def __str__(self):
        return self.name
```


TableView Definition

```
from .models import Customer
from generic.table import TableView
class CustomerTableView(TableView):
    model = Customer
    extend_html = 'customers/index.html' # Need {% block content %}{% endblock %}
    columns = [('name', 'Name'),('email', 'Email'),('birthdate', 'Birthdate')]
    search_able = True
    search_by = [('name__icontains',''), ('email__icontains','')]
    reset_able = True
```

TableView Definition with GridView
```
from .models import Customer
from generic.table import TableView
from generic.grid import GridView
class CustomerTableView(TableView):
    model = Customer
    extend_html = 'customers/index.html'
    columns = [('name', 'Name'), ('email', 'Email'), ('birthdate', 'Birthdate')]
    search_able = True
    search_by = [('name__icontains',''), ('email__icontains','')]
    reset_able = True
    link_to_detail = True
    detail_view_name = 'customer_grid_view'
    create_able = True
    delete_able = True
    
class CustomerGridView(GridView):
    model = Customer
    extend_html = 'customers/index.html'
    back_able = True
    back_view = 'customer_table_view'
    edit_able = True
```
Or defining a grid
```
class CustomerGridView(GridView):
    model = Customer
    extend_html = 'customers/index.html'
    back_able = True
    back_view = 'customer_table_view'
    edit_able = True
    grid = [('name', 1),('email', 1),('address', 2),('birthdate', 3)]
```


URLConf
```
from .views import CustomerTableView, CustomerGridView
app_name = 'customer'    # Need app_name
urlpatterns = [
    url(r'^(?P<pk>[0-9]+)/Customer/$', CustomerGridView.as_view(), name='customer_grid_view'),
    url(r'^NewCustomer/$', CustomerGridView.as_view(), name='customer_grid_view'),
    url(r'^', CustomerTableView.as_view(), name='customer_table_view'),
]
```

