window.addEventListener("load", (event) => {
    var openSvg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" class="design-iconfont"><path d="M27.8832966,16.887873 C27.8094879,16.8666413 27.7342507,16.8550603 27.660442,16.8492698 C27.6742514,16.6663873 27.6537754,16.4864 27.6023474,16.3204063 C27.639966,15.9363048 27.6666324,15.5497905 27.6666324,15.1555556 C27.6666324,8.62631111 22.4433584,3.33333333 16.0000982,3.33333333 C9.55636184,3.33333333 4.33356399,8.62631111 4.33356399,15.1555556 C4.33356399,15.5497905 4.35975417,15.9363048 4.39784898,16.3204063 C4.34594481,16.4864 4.32546885,16.6663873 4.33927822,16.8492698 C4.26546953,16.8550603 4.19070847,16.8666413 4.11689979,16.887873 L3.54452533,17.0519365 C2.91310393,17.2333714 2.5378701,17.9287111 2.70739198,18.6052317 L3.93356854,23.5044571 C4.10261424,24.1804952 4.75213067,24.5819683 5.38355207,24.4010159 L5.95545034,24.2374349 C5.98925948,24.2273016 6.01973533,24.2104127 6.05211591,24.1978667 L6.08925835,24.3561397 C6.20497132,24.8468825 6.56068156,25.1885206 6.97448639,25.2681397 C9.50064818,28.5822222 13.7929804,28.6932063 14.8982059,28.6628063 C14.9120153,28.6632889 14.9248723,28.6666667 14.9386817,28.6666667 L17.0962762,28.6666667 C17.8910291,28.6666667 18.5353075,28.0996825 18.5353075,27.4 C18.5353075,26.7008 17.8910291,26.1333333 17.0962762,26.1333333 L14.9386817,26.1333333 C14.1439288,26.1333333 13.5001266,26.7008 13.5001266,27.4 C13.5001266,27.5119492 13.5220311,27.6181079 13.5525069,27.7213714 C10.7211105,27.3300317 8.98255883,25.9687873 8.10447356,25.0447238 L8.51304035,24.9207111 C9.10303365,24.7407238 9.45350586,24.0506921 9.29541242,23.3794794 L7.57733669,16.0887873 C7.44210013,15.5136 6.9773435,15.142527 6.47639681,15.1594159 L6.47639681,15.1555556 C6.47639681,9.82542222 10.7401579,5.5047619 16.0000982,5.5047619 C21.2600385,5.5047619 25.5237996,9.82542222 25.5237996,15.1555556 L25.5237996,15.1594159 C25.0223767,15.142527 24.5576201,15.5136 24.4223835,16.0887873 L22.704784,23.3794794 C22.5466905,24.0506921 22.8966866,24.7407238 23.4866799,24.9207111 L24.5557153,25.2454603 C25.1457086,25.4259302 25.7523684,25.0273524 25.9104619,24.3561397 L25.9476043,24.1978667 C25.9804611,24.2104127 26.0104607,24.2273016 26.044746,24.2374349 L26.6166443,24.4010159 C27.2480657,24.5819683 27.897106,24.1804952 28.0666279,23.5044571 L29.2928044,18.6052317 C29.4618501,17.9287111 29.0866163,17.2333714 28.4551949,17.0519365 L27.8832966,16.887873 Z" fill="#FFF" fill-rule="evenodd"/></svg>';
    var closeSvg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" class="design-iconfont"><path d="M6.95955989,6.95955989 C7.35008418,6.56903559 7.98324916,6.56903559 8.37377345,6.95955989 L15.9996667,14.5846667 L23.6262266,6.95955989 C24.0167508,6.56903559 24.6499158,6.56903559 25.0404401,6.95955989 C25.4309644,7.35008418 25.4309644,7.98324916 25.0404401,8.37377345 L17.4136667,15.9996667 L25.0404401,23.6262266 C25.4009241,23.9867105 25.4286536,24.5539416 25.1236287,24.9462328 L25.0404401,25.0404401 C24.6499158,25.4309644 24.0167508,25.4309644 23.6262266,25.0404401 L15.9996667,17.4136667 L8.37377345,25.0404401 C7.98324916,25.4309644 7.35008418,25.4309644 6.95955989,25.0404401 C6.56903559,24.6499158 6.56903559,24.0167508 6.95955989,23.6262266 L14.5846667,15.9996667 L6.95955989,8.37377345 C6.59907592,8.01328949 6.57134639,7.44605843 6.87637128,7.05376722 Z" fill="#FFF" fill-rule="evenodd"/></svg>';
    var config = {
        "parentClass": "",
        "btnSize": 56,
        "btnLeft": "",
        "btnRight": 30,
        "btnTop": "",
        "btnBottom": 30,
        // --- MODIFICATION: Point to your local chat.html ---
        "liveChatUrl": '/static/chat.html',
        "liveChatWidth": 400,
        "liveChatHeight": 600,
        "expandDire": ""
    };
    initLiveChat(config);

    function initLiveChat(config) {
        var bodyDom = document.body;
        if (config.parentClass) {
            bodyDom = document.querySelector('.' + config.parentClass);
        }
        if (!bodyDom.style.position) {
            bodyDom.style.position = 'relative';
        }
        var entryBtn = document.createElement('div');
        entryBtn.className = 'live-chat-entry close';
        btnInitStyle();
        btnCloseStyle();
        bodyDom.appendChild(entryBtn);
        entryBtn.onclick = function() {
            var liveChatIframe = document.getElementById('liveChatIframe');
            if (this.classList.contains('close')) {
                this.classList.remove('close');
                this.classList.add('open');
                btnOpenStyle();
                if (liveChatIframe) {
                    iframeOpenStyle(liveChatIframe);
                } else {
                    iframeInit();
                }
            } else {
                this.classList.remove('open');
                this.classList.add('close');
                btnCloseStyle();
                if (liveChatIframe) {
                    iframeCloseStyle(liveChatIframe);
                }
            }
        };
        entryBtn.addEventListener('mouseover', () => { entryBtn.style.backgroundColor = '#4299FC'; });
        entryBtn.addEventListener('mouseout', () => { entryBtn.style.backgroundColor = '#3F8EF0'; });

        function btnInitStyle() {
            // --- MODIFICATION: Use 'fixed' positioning ---
            entryBtn.style.position = 'fixed';
            entryBtn.style.top = typeof config.btnTop === 'number' && config.btnTop >= 0 ? config.btnTop + 'px' : 'auto';
            entryBtn.style.left = typeof config.btnLeft === 'number' && config.btnLeft >= 0 ? config.btnLeft + 'px' : 'auto';
            entryBtn.style.bottom = typeof config.btnBottom === 'number' && config.btnBottom >= 0 ? config.btnBottom + 'px' : 'auto';
            entryBtn.style.right = typeof config.btnRight === 'number' && config.btnRight >= 0 ? config.btnRight + 'px' : 'auto';
            entryBtn.style.width = config.btnSize >= 0 ? config.btnSize + 'px' : '50px';
            entryBtn.style.height = config.btnSize >= 0 ? config.btnSize + 'px' : '50px';
            entryBtn.style.borderRadius = config.btnSize >= 0 ? config.btnSize / 2 + 'px' : '25px';
            entryBtn.style.backgroundColor = '#00E676';
            entryBtn.style.padding = '12px';
            entryBtn.style.cursor = 'pointer';
            entryBtn.style.userSelect = 'none';
            entryBtn.style.boxSizing = 'border-box';
            entryBtn.style.zIndex = 100000;
            entryBtn.innerHTML = openSvg + closeSvg;
        }

        function btnCloseStyle() {
            entryBtn.querySelectorAll('svg')[0].style.display = 'block';
            entryBtn.querySelectorAll('svg')[1].style.display = 'none';
        }

        function btnOpenStyle() {
            entryBtn.querySelectorAll('svg')[0].style.display = 'none';
            entryBtn.querySelectorAll('svg')[1].style.display = 'block';
        }

        function iframeInit() {
            var iframeBox = document.createElement('iframe');
            var iframeWidth = typeof config.liveChatWidth === 'number' && config.liveChatWidth >= 0 ? config.liveChatWidth : '';
            var iframeHeight = typeof config.liveChatHeight === 'number' && config.liveChatHeight >= 0 ? config.liveChatHeight : '';
            iframeBox.id = 'liveChatIframe';
            iframeBox.src = config.liveChatUrl;
            iframeBox.style.position = 'absolute'; // Positioned relative to the button
            iframeBox.style.width = iframeWidth ? iframeWidth + 'px' : '100%';
            iframeBox.style.height = iframeHeight ? iframeHeight + 'px' : '100%';
            iframeBox.style.bottom = (config.btnSize + 10) + 'px'; // Position above button
            iframeBox.style.right = '0px';
            iframeBox.style.boxShadow = '0 5px 20px rgba(0,0,0,0.2)';
            iframeBox.style.borderRadius = '12px';
            iframeBox.style.border = 'none';
            iframeBox.style.opacity = '1';
            iframeBox.style.transition = 'opacity 0.3s ease';
            entryBtn.appendChild(iframeBox);
        }

        function iframeCloseStyle(liveChatIframe) {
            liveChatIframe.style.opacity = '0';
            setTimeout(() => { liveChatIframe.style.display = 'none'; }, 300);
        }

        function iframeOpenStyle(liveChatIframe) {
            liveChatIframe.style.display = 'block';
            setTimeout(() => { liveChatIframe.style.opacity = '1'; }, 10);
        }
    }
});