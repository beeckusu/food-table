from django.shortcuts import render
from django.http import HttpResponse
import sys

# Create your views here.

def ft6_sample(request):
    import os
    return HttpResponse(f"""
        <html>
            <head><title>FT-6 Sample Page</title></head>
            <body style="font-family: Arial; padding: 50px; background: #f3e5f5;">
                <h1 style="color: #6a1b9a; font-size: 48px;">🟣 FT-6 PURPLE PAGE 🟣</h1>
                <p style="font-size: 24px;">This page is running from the <strong>Food-Table-second</strong> directory on branch <strong>FT-6</strong>.</p>
                <p style="font-size: 20px;">Working Directory: {os.getcwd()}</p>
                <p style="font-size: 20px;">Expected Port: 8001</p>
                <p style="font-size: 20px;">Python File: {__file__}</p>
                <p style="font-size: 20px;">Module Path: {sys.modules[__name__].__file__}</p>
                <p style="margin-top: 30px; padding: 20px; background: white; border-left: 4px solid #6a1b9a; font-size: 18px;">
                    <strong>Note:</strong> This is a completely separate branch with independent code!
                </p>
            </body>
        </html>
    """)
