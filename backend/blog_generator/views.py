from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from pytube import YouTube
from django.conf import settings
import os
import assemblyai as aai
import openai 

# Create your views here.
@login_required
def index(request):
    return render(request, 'index.html')

@csrf_exempt
def generate_blog(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            yt_link = data['link'] 
            return JsonResponse({'content': yt_link})
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error':'Invalid data sent'}, status=400)
        
        # get yt title
        title =  yt_title(yt_link)

        # get transcript
        transcription = get_transcription(yt_link)
        if not transcription:
            return JsonResponse({'error':'Failed to get transcript'}, status = 500)

        # use openAI to generate the blog
        blog_content = generate_blog_from_transcription(transcription)
        if not blog_content:
            return JsonResponse({'error':'Failed to generate blog article'}, status=500)

        # save blog article to database


        # return blog article as a response
        return JsonResponse({'content': blog_content})

    else:
        return JsonResponse({'error':'Invalid request method'}, status=405)

def yt_title(link):
    yt = YouTube(link)
    title = yt.title
    return title

# Download Audio to System
def download_audio(link):
    yt = YouTube(link)
    video = yt.streams.filter(only_audio=True).first()
    out_file = video.download(output_path=settings.MEDIA_ROOT)
    base, ext = os.path.splitext(out_file)
    new_file = base + '.mp3'
    os.rename(out_file,new_file)
    return new_file


def get_transcription(link):
    audio_file = download_audio(link)
    aai.settings.api_key = "675e7efb03a64ab79d4745b6248afc24"

    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_file)

    return transcriber.text

def generate_blog_from_transcription(transcription):
    openai.api_key = "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"

    prompt = f"Based on the following transcript from a YouTube video, write a comprehensive blog article, write it based on the transcript, but dont make it look like a youtube video, make it look like a proper blog article:\n\n{transcription}\n\nArticle:"

    response = openai.completions.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=1000
    )

    generated_conent = response.choices[0].text.strip()

    return generated_conent



# Login Form
def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request,username=username, password=password)
        if user is not None:
            login(request,user)
            return redirect('/')
        else:
            error_message = "Invalid Username or Password"
            return render(request,'login.html',{'error_message':error_message})
    return render(request, 'login.html')


# Signup Form
def user_signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirmPassword = request.POST['confirmPassword']

        if password == confirmPassword:
            try:
                user = User.objects.create_user(username,email,password)
                user.save()
                login(request,user)
                return redirect('/')
            except:
                error_message = 'Error Creating Account'
                return render(request,'signup.html', {'error_message':error_message})    
            
        else:
            error_message = 'Password not match'
            return render(request,'signup.html', {'error_message':error_message})    
    return render(request, 'signup.html')


def user_logout(request):
    logout(request)
    return redirect('/')
