from django.contrib.contenttypes.models import ContentType
import simplejson as json

from coffin.views.generic import TemplateView, DetailView, ListView
from webui.controller.models import Dataset, Source, Aggregator

from webui.scheduler.models import Scheduler


class SchedulerResultDetailView(TemplateView):
    template_name = 'scheduler/run_result.html'

    def get_context_data(self, **kwargs):
        from redis import Redis
        from .log import get_redis_key, END
        from util import AttrDict

        data = \
            super(SchedulerResultDetailView, self).get_context_data(**kwargs)

        red = Redis()
        task_id = self.kwargs['task_id']

        try:
            # all the objects should have the same content type, here...
            object_list = [
                scheduler.content_object for scheduler in
                Scheduler.objects.filter(logger_name=task_id)
            ]

            object_type_name = type(object_list[0]).__name__.lower()
            data[object_type_name + '_list'] = object_list
            if isinstance(object_list[0], Dataset):
                data['source'] = data['dataset_list'][0].source

        except IndexError:
            dataset_pk = self.request.GET.get('dataset')
            source_pk = self.request.GET.get('source')

            if dataset_pk:
                data['dataset_list'] = Dataset.objects.filter(pk=dataset_pk)
                data['source'] = data['dataset_list'][0].source
            elif source_pk:
                data['source'] = Source.objects.get(pk=source_pk)
                data['dataset_list'] = data['source'].datasets.all()
            else:
                pass

        key = get_redis_key(task_id)
        logs = []
        start = max(int(self.request.GET.get('start', 0)), 0)
        for idx, log in enumerate(red.lrange(key, start, -1)):
            log_dict = AttrDict(json.loads(log))
            log_dict.index = start + idx
            log_dict.show_args = False

            try:
                if isinstance(log_dict.args, dict):
                    args = (log_dict.args,)
                else:
                    args = tuple(log_dict.args)
                log_dict.msg = log_dict.msg % args
            except:  # pylint: disable=W0702
                log_dict.show_args = True

            logs.append(log_dict)
        data['logs'] = logs
        data['task_id'] = task_id

        if self.request.is_ajax():
            data['parent'] = 'layout/ajax.html'
        else:
            data['parent'] = 'layout/site_base.html'

        data['END'] = END

        return data
scheduler_result_detail_view = SchedulerResultDetailView.as_view()


# class SchedulerResultListView(ListView):
#     model = TaskState

class SchedulerDetailView(DetailView):
    model = Scheduler
    template_name = 'scheduler/scheduler/detail.html'
scheduler_detail = SchedulerDetailView.as_view()


class SchedulerListView(ListView):
    model = Scheduler
    template_name = 'scheduler/scheduler/list.html'
    paginate_by = 10

    def get_queryset(self):
        request = self.request
        filter_model = request.GET.get('model')
        filter_pk = request.GET.get('pk')

        queryset = self.model.objects.all()

        if filter_model and filter_pk:
            filter_model = filter_model.lower()
            if filter_model == 'source':
                ctype = ContentType.objects.filter(model='dataset')
                pks = Dataset.objects.filter(source_id=filter_pk)
            else:
                ctype = ContentType.objects.filter(model=filter_model)
                pks = (filter_pk, )

            try:
                queryset = queryset.filter(
                    content_type__in=ctype,
                    object_id__in=pks
                )
            except ContentType.DoesNotExist:
                return ()

        return queryset

scheduler_list = SchedulerListView.as_view()


# scheduler_result_list_view = SchedulerResultListView.as_view()
