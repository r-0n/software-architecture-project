from django.urls import path
from . import views

app_name = "returns"

urlpatterns = [
    path("", views.rma_list, name="rma_list"),
    path("create/<int:sale_id>/", views.create_rma, name="create_rma"),
    path("<int:rma_id>/", views.rma_detail, name="rma_detail"),
    path("<int:rma_id>/approve/", views.rma_approve, name="rma_approve"),
    path("<int:rma_id>/approve-inspection/", views.rma_approve_after_inspection, name="rma_approve_after_inspection"),
    path("<int:rma_id>/receive/", views.rma_receive, name="rma_receive"),
    path("<int:rma_id>/refund/", views.rma_refund, name="rma_refund"),
    path("<int:rma_id>/close/", views.rma_close, name="rma_close"),
    path("<int:rma_id>/cancel/", views.rma_cancel_request, name="rma_cancel_request"),
    path("<int:rma_id>/item-returned/", views.rma_item_returned, name="rma_item_returned"),
    path("<int:rma_id>/choose-resolution/", views.rma_choose_resolution, name="rma_choose_resolution"),
]

