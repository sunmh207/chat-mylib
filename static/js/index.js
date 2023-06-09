const API_URL = "/completions";
const messagsEle = document.getElementsByClassName("messages")[0];
const chatlog = document.getElementById("chatlog");
const sendBtnEle = document.getElementById("sendbutton");
const textarea = document.getElementById("chatinput");
const uploadBtnEle = document.getElementById("fileInput");
textarea.focus();
let data = [];
let loading = false;
const md = markdownit({
    highlight: function (str, lang) { // markdown高亮
        try {
            return hljs.highlightAuto(str).value;
        } catch (__) { }

        return ""; // use external default escaping
    }
});
md.use(texmath, { // markdown katex公式
    engine: katex,
    delimiters: 'dollars',
    katexOptions: {macros: {"\\RR": "\\mathbb{R}"}}
});
const x = {
    getCodeLang(str = '') {
        const res = str.match(/ class="language-(.*?)"/);
        return (res && res[1]) || '';
    },
    getFragment(str = '') {
        return str ? `<span class="u-mdic-copy-code_lang">${str}</span>` : '';
    },
};
const strEncode = (str = '') => {
    if (!str || str.length === 0) {
        return '';
    }
    return str
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/'/g, '\'')
        .replace(/"/g, '&quot;');
};
const getCodeLangFragment = (oriStr = '') => {
    return x.getFragment(x.getCodeLang(oriStr));
};
const copyClickCode = (ele) => {
    const input = document.createElement('textarea');
    input.value = ele.dataset.mdicContent;
    const nDom = ele.previousElementSibling;
    const nDelay = ele.dataset.mdicNotifyDelay;
    const cDom = nDom.previousElementSibling;
    document.body.appendChild(input);
    input.select();
    input.setSelectionRange(0, 9999);
    document.execCommand('copy');
    document.body.removeChild(input);
    if (nDom.style.display === 'none') {
        nDom.style.display = 'block';
        cDom && (cDom.style.display = 'none');
        setTimeout(() => {
            nDom.style.display = 'none';
            cDom && (cDom.style.display = 'block');
        }, nDelay);
    }
};
const enhanceCode = (render, options = {}) => (...args) => {
    /* args = [tokens, idx, options, env, slf] */
    const {
        btnText = '复制代码', // button text
        successText = '复制成功', // copy-success text
        successTextDelay = 2000, // successText show time [ms]
        showCodeLanguage = true, // false | show code language
    } = options;
    const [tokens = {}, idx = 0] = args;
    const cont = strEncode(tokens[idx].content || '');
    const originResult = render.apply(this, args);
    const langFrag = showCodeLanguage ? getCodeLangFragment(originResult) : '';
    const tpls = [
        '<div class="m-mdic-copy-wrapper">',
        `${langFrag}`,
        `<div class="u-mdic-copy-notify" style="display:none;">${successText}</div>`,
        '<button ',
        'class="u-mdic-copy-btn j-mdic-copy-btn" ',
        `data-mdic-content="${cont}" `,
        `data-mdic-notify-delay="${successTextDelay}" `,
        `onclick="copyClickCode(this)">${btnText}</button>`,
        '</div>',
    ];
    const LAST_TAG = '</pre>';
    const newResult = originResult.replace(LAST_TAG, `${tpls.join('')}${LAST_TAG}`);
    return newResult;
};

const codeBlockRender = md.renderer.rules.code_block;
const fenceRender = md.renderer.rules.fence;
md.renderer.rules.code_block = enhanceCode(codeBlockRender);
md.renderer.rules.fence = enhanceCode(fenceRender);

md.renderer.rules.image = function (tokens, idx, options, env, slf) {
    var token = tokens[idx];
    token.attrs[token.attrIndex("alt")][1] = slf.renderInlineAsText(token.children, options, env);
    token.attrSet("onload", "messagsEle.scrollTo(0, messagsEle.scrollHeight);this.removeAttribute('onload')");
    return slf.renderToken(tokens, idx, options)
}
document.getElementById("clearConv").onclick = () => {
    if (!loading) {
        data = [];
        chatlog.innerHTML = "";
    }
}
const endAction = () => {
    loading = false;
    sendBtnEle.disabled = false;
    sendBtnEle.classList.remove("loading");
    sendBtnEle.classList.add("loaded");
}
let currentResEle;
let progressData = "";
let lastStr = "";


//向服务器发送请求
const sendPrompt = async () => {
  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });
    if (response.ok) {
      const result = await response.json();
      if (result.status === "success") {
        const answer = result.data.result.message;
        const refs = result.data.result.refs;
        let link = "参考资料:";
        if (Array.isArray(refs)) {
          link += refs.map((ref, index) => {
            const href = `/preview/${ref.resource_id}`;
            const separator = (index === refs.length - 1) ? "" : "| ";
            return `<a href="${href}" target="_blank">${ref.resource_name}</a>${separator}`;
          }).join("");
        }
        data.push({
          role: "assistant",
          content: answer
        });
        currentResEle = document.createElement("div");
        currentResEle.className = "response markdown-body";
        currentResEle.innerHTML = `${md.render(answer)}${link}`;
        chatlog.appendChild(currentResEle);
        messagsEle.scrollTo(0, messagsEle.scrollHeight);
      } else {
        alert(result.data.message);
      }
      endAction();
    } else {
      endAction();
      alert('请求失败');
    }
  } catch (error) {
    console.error(error);
  }
};

const generateText = (message) => {
    loading = true;
    sendBtnEle.disabled = true;
    sendBtnEle.classList.remove("loaded");
    sendBtnEle.classList.add("loading");
    //将发送数据存储到data
    data.push({role: "user", content: message.trim()});
    let request = document.createElement("div");
    request.className = "markdown-body";
    request.innerHTML = md.render(message);
    chatlog.appendChild(request);
    messagsEle.scrollTo(0, messagsEle.scrollHeight);
    sendPrompt();
};

textarea.onkeydown = (event) => {
    if (event.keyCode === 13) {
        if (!event.shiftKey) {
            event.preventDefault();
            genFunc();
        }
    }
}
textarea.oninput = (e) => {
    textarea.style.height = "50px";
    textarea.style.height = e.target.scrollHeight + "px";
};
const genFunc = function () {
    let message = textarea.value;
    if (message.length < 1) {
        return;
    } else {
        if (loading === true) {
            return;
        }
        textarea.value = "";
        textarea.style.height = "50px";
        generateText(message);
    }
}

//上传资料
const upload = function(){
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    if (!file) {
        alert('请选择文件');
        return;
    }
    if (file.size > 10 * 1024 * 1024) {
        alert('文件大小不能超过10M');
        return;
    }
    showSpinner();
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/upload', true);
    xhr.setRequestHeader('cache', false);
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                var res = JSON.parse(xhr.responseText);
                if(res.status == "success"){
                    var msg = "文件摘要："+res.data.summary;
                    currentResEle = document.createElement("div");
                    currentResEle.className = "response markdown-body";
                    currentResEle.innerHTML = md.render(msg);
                    chatlog.appendChild(currentResEle);
                    messagsEle.scrollTo(0, messagsEle.scrollHeight);
                    alert("文件上传成功");
                }else{
                    alert(res.data.message)
                }
            } else {
                alert('文件上传失败');
            }
            stopSpinner();
        }
    };
    const formData = new FormData();
    formData.append('file', file);
    xhr.send(formData);
}

const gotoAdmin = function(){
    window.open("/admin","_blank");
}
const feedback = function(){
     window.open("https://support.qq.com/product/538086","_blank");
}
const setKey = function(){
    const userInput = prompt("请输入您的OpenAI API Key:");
    if (userInput != null) {
        const xhr = new XMLHttpRequest();
        const url = "/setkey";
        const data =  `key=${userInput}` ;
        xhr.open("POST", url, true);
        xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                console.log(xhr.responseText);
                alert(xhr.responseText);
            }
        };
        xhr.send(data);
    }
}
//发送按钮点击事件
sendBtnEle.onclick = genFunc;
//上传资料按钮事件
uploadBtnEle.onchange = upload;

const showSpinner = function(){
    var btn = document.getElementById("fileInput");
    var loading = document.getElementById("loading");
    var overlay = document.getElementById("overlay");
    btn.disabled = true;
    loading.style.display = "block";
    overlay.style.display = "block";
}
const stopSpinner = function(){
    var btn = document.getElementById("fileInput");
    var loading = document.getElementById("loading");
    var overlay = document.getElementById("overlay");
    btn.disabled = false;
    loading.style.display = "none";
    overlay.style.display = "none";
}

