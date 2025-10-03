from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import yt_dlp
from django.conf import settings
import os
import assemblyai as aai
import openai 
from urllib.error import HTTPError
from googleapiclient.discovery import build
import re

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


YOUTUBE_API_KEY = "AIzaSyAE0k--WmwXY9jm2_1YVk0fB1VDG1ua6Rw"
def yt_title(link):
    video_id = extract_video_id(link)
    if not video_id:
        return "Link YouTube không hợp lệ"

    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        request = youtube.videos().list(
            part="snippet",
            id=video_id
        )
        response = request.execute()
        
        if response["items"]:
            return response["items"][0]["snippet"]["title"]
        else:
            return "Không tìm thấy video"
    except Exception as e:
        print("YouTube API Error:", e)
        return "Không lấy được tiêu đề"

# Download Audio to System
def download_audio(link):
    output_path = os.path.join(settings.MEDIA_ROOT, "%(id)s.%(ext)s")
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'ffmpeg_location': r"D:\Coding_Design\ffmpeg\bin",  
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(link, download=True)
        return os.path.join(settings.MEDIA_ROOT, f"{info_dict['id']}.mp3")

def extract_video_id(url):
    regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(regex, url)
    return match.group(1) if match else None

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
