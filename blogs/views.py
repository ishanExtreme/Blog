from django.shortcuts import render
from .models import Blogs
from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger
from django.shortcuts import get_object_or_404
from .forms import CommentForm,SearchForm
from taggit.models import Tag
from django.db.models import Count

from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank

def home(request,tag_slug = None):
    object_list = Blogs.published.all().order_by('-publish')
    tag = None
    all_tag = Tag.objects.all()
    if tag_slug:
        tag = get_object_or_404(Tag,slug = tag_slug)
        object_list = object_list.filter(tags__in=[tag])
    paginator = Paginator(object_list,3)
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)

    
    form = SearchForm()
    query = None
    results = []
    if 'search' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['search']
            search_vector = SearchVector('title', weight='A') + SearchVector('body', weight='B') 
            search_query = SearchQuery(query)

            results = Blogs.objects.annotate( rank=SearchRank(search_vector, search_query) ).filter(rank__gte=0.3).order_by('-rank')
            return render(request,'blogs/search.html',{'form':form,'results':results,'query':query,})
    return render(request,'blogs/home.html',{'posts':posts,'tag':tag,'tags':all_tag,'form':form,'results':results,'query':query})

def detail(request,year,month,day,post):
    post = get_object_or_404(Blogs,slug=post,status='published',publish__year=year,publish__month=month,publish__day=day)
    latest_posts = Blogs.published.all().order_by('-publish')[:3]
    all_tag = Tag.objects.all()
    comments = post.comments.filter(active = True)
    new_comment = None
    if request.method == 'POST':
        comment_form = CommentForm(data = request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit = False)
            new_comment.post = post
            new_comment.save()
    else:
        comment_form = CommentForm()
    post_tags_ids = post.tags.values_list('id',flat = True)
    similar_posts = Blogs.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags','-publish')[:4]
    
    
    return render(request,'blogs/detail.html',{'post':post,'latest_posts':latest_posts,'comments':comments,'new_comment':new_comment,'comment_form':comment_form,'tags':all_tag,'similar_posts':similar_posts,})




# Create your views here.
