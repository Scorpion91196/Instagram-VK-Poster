from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from django.views import View

from instaparser.agents import WebAgent, Media
from instaparser.entities import Account
from insta_vk_main.models import CustomUser
import datetime


class InstaGroupView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            insta_group = kwargs.get('insta_group')
            agent = WebAgent()
            account = Account(insta_group)
            agent.update(account)
            media = agent.get_media(account, count=20)
            posts = []
            for m in media[0]:
                m.date = datetime.date.fromtimestamp(m.date)
                if m.date == datetime.date.today():
                    m.date = 'Сегодня'
                posts.append(m)
            user_insta_groups = CustomUser.objects.get(username=request.user.username).user_settings.insta_group_list.all()
            context = {
                'posts': posts,
                'user_insta_groups': user_insta_groups
            }
            return render(request, 'insta-group-content.html', context)
        else:
            return HttpResponseRedirect('login')


