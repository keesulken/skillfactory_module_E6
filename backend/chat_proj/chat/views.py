from django.db import IntegrityError
from django.views.generic import CreateView
from rest_framework import generics, viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from django.contrib.auth import get_user_model

from .serializers import *
from .forms import *

User = get_user_model()


class RegisterView(CreateView):
    model = User
    form_class = BaseRegisterForm
    success_url = '/'


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class ChatRoomViewSet(viewsets.ModelViewSet):
    queryset = ChatRoom.objects.all()
    serializer_class = ChatRoomSerializer


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer


class ChatDetailAPIView(APIView):
    def get(self, request, **kwargs):
        chat = ChatRoom.objects.get(pk=kwargs['pk'])
        if chat.private:
            user_list = chat.user_list.all()
            msg_list = Message.objects.filter(chat=chat)
            chat_data = SingleChatSerializer(chat).data
            msg_list_data = MessageSerializer(msg_list, many=True).data
            user_list_data = UserSerializer(user_list, many=True).data
            return Response({'chat': chat_data,
                             'users': user_list_data,
                             'messages': msg_list_data})
        else:
            admin = User.objects.get(pk=chat.admin_id)
            user_list = chat.user_list.all()
            msg_list = Message.objects.filter(chat=chat)
            chat_data = SingleChatSerializer(chat).data
            admin_data = UserSerializer(admin).data
            msg_list_data = MessageSerializer(msg_list, many=True).data
            user_list_data = UserSerializer(user_list, many=True).data
            return Response({'chat': chat_data,
                             'admin': admin_data,
                             'users': user_list_data,
                             'messages': msg_list_data})


class ProfileAPIView(APIView):
    def get(self, request, **kwargs):
        user = request.user
        profile_data = UserSerializer(user).data
        if len(user.chatroom_set.all()) == 0:
            return Response({'user': profile_data,
                             'chat': 'null'})
        elif len(user.chatroom_set.all()) == 1:
            chat = user.chatroom_set.all().first()
            chat_data = ChatRoomSerializer(chat).data
            return Response({'user': profile_data,
                             'chat': chat_data})
        else:
            raw_chat_list = user.chatroom_set.all()
            chat_list = ChatRoomSerializer(raw_chat_list, many=True).data
            return Response({'user': profile_data,
                             'chat_list': chat_list})


class NewMessageAPIView(APIView):
    def post(self, request, **kwargs):
        msg = Message()
        msg.author = User.objects.get(username=request.data['user'])
        msg.chat = ChatRoom.objects.get(pk=kwargs['chat_id'])
        msg.content = request.data['text']
        msg.save()
        return Response(status=status.HTTP_201_CREATED)


class UserChatAPIView(APIView):
    def get(self, request, **kwargs):
        user = User.objects.get(id=kwargs['user_id'])
        chats = []
        for i in ChatRoom.objects.all():
            if user in i.user_list.all():
                chats.append(i)
        chat_list = ChatRoomSerializer(chats, many=True).data
        return Response({'chats': chat_list})


class NewChatAPIView(APIView):
    def post(self, request, **kwargs):
        chat = ChatRoom()
        admin = User.objects.get(username=request.data['admin'])
        chat.name = request.data['name']
        chat.description = request.data['desc']
        chat.admin_id = admin.id
        chat.save()
        chat.user_list.add(admin)
        return Response({'id': chat.pk}, status=status.HTTP_201_CREATED)


class NewPrivateChatAPIView(APIView):
    def post(self, request, **kwargs):
        chat = ChatRoom()
        companion1 = User.objects.get(pk=request.data['init'])
        companion2 = User.objects.get(pk=request.data['companion'])
        chat.name = f'{companion1.pk}to{companion2.pk}'
        chat.admin_id = 0
        chat.private = True
        chat.save()
        chat.user_list.add(companion1)
        chat.user_list.add(companion2)
        return Response({'id': chat.pk}, status=status.HTTP_201_CREATED)


class AddNewUserToChatAPIView(APIView):
    def patch(self, request, **kwargs):
        chat = ChatRoom.objects.get(pk=kwargs['chat_id'])
        new_user = User.objects.get(username=request.data['username'])
        chat.user_list.add(new_user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AddUserPictureAPIView(APIView):
    def post(self, request, **kwargs):
        user = User.objects.get(pk=kwargs['user_id'])
        user.picture = request.data['file']
        user.save()
        pic = UserSerializer(user).data['picture']
        return Response({'img': pic}, status=status.HTTP_200_OK)


class UserChangeNameAPIView(APIView):
    def post(self, request, **kwargs):
        user = User.objects.get(pk=kwargs['user_id'])
        try:
            user.username = request.data['name']
            user.save()
            return Response({'username': user.username}, status=status.HTTP_200_OK)
        except IntegrityError:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class LeaveChatAPIView(APIView):
    def patch(self, request, **kwargs):
        user = User.objects.get(username=request.data['user'])
        chat = ChatRoom.objects.get(pk=kwargs['chat_id'])
        chat.user_list.remove(user)
        chat.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
