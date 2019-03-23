from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from django.views import View

from instaparser.agents import Agent, Media
from instaparser.entities import Account

import datetime


class InstaGroupView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            insta_group = kwargs.get('insta_group')
            agent = Agent()
            account = Account(insta_group)
            agent.update(account)
            media = agent.get_media(account, count=20)
            posts = []
            for m in media[0]:
                m.date = datetime.date.fromtimestamp(m.date)
                if m.date == datetime.date.today():
                    m.date = 'Сегодня'
                posts.append(m)
            context = {
                'posts': posts
            }
            return render(request, 'insta-group-content.html', context)
        else:
            return HttpResponseRedirect('login')


