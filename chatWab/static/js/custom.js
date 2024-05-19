hljs.initHighlightingOnLoad();

function scrollToBottom() {
    const chatHistory = document.querySelector('.chat-history');
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

document.getElementById('chat-form').addEventListener('submit', async function (event) {
    event.preventDefault();
    const userInput = document.getElementById('user_input').value;
    const chatHistory = document.querySelector('.chat-history');

    // 添加用户消息到聊天记录
    const userMessageDiv = document.createElement('div');
    userMessageDiv.className = 'message user';
    userMessageDiv.innerHTML = `<img src="/static/img/user.png" alt="user avatar" class="avatar">
                                <div class="content"><pre><code>${userInput}</code></pre></div>`;
    chatHistory.appendChild(userMessageDiv);

    // 添加加载中的系统消息
    const loadingMessageDiv = document.createElement('div');
    loadingMessageDiv.className = 'message system';
    loadingMessageDiv.innerHTML = `<img src="/static/img/system.png" alt="system avatar" class="avatar">
                                   <div class="content"><div class="loading"></div></div>`;
    chatHistory.appendChild(loadingMessageDiv);

    // 滚动到底部
    scrollToBottom();

    try {
        // 发送用户输入到服务器
        const response = await fetch('/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ user_input: userInput })
        });

        if (response.ok) {
            const data = await response.json();

            // 更新系统消息
            loadingMessageDiv.querySelector('.content').innerHTML = `<pre><code>${data.system_message}</code></pre>`;
            hljs.highlightBlock(loadingMessageDiv.querySelector('code'));
        } else {
            throw new Error('Network response was not ok');
        }
    } catch (error) {
        console.error('Fetch error:', error);
        loadingMessageDiv.querySelector('.content').innerHTML = `<pre><code>系统消息加载失败，请稍后重试。</code></pre>`;
    }

    // 清空输入框
    document.getElementById('user_input').value = '';

    // 滚动到底部
    scrollToBottom();
});

scrollToBottom();

