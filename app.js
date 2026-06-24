let tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

// Rasmga mos ranglar
tg.setHeaderColor('#F5F2EA');
tg.setBackgroundColor('#F5F2EA');

let products = [];
let cart = {};
let currentCategory = 'Barchasi';

async function loadProducts() {
    try {
        let res = await fetch(`products.json?t=${new Date().getTime()}`);
        let data = await res.json();
        products = data.products || [];
        window.allCategories = data.categories || [];
        renderTabs();
        renderProducts();
    } catch(e) {
        console.error("Maxsulotlarni yuklashda xatolik", e);
    }
}

function formatPrice(price) {
    return price.toLocaleString('ru-RU');
}

function renderTabs() {
    const tabsContainer = document.getElementById("category-tabs");
    if(!tabsContainer) return;
    
    tabsContainer.innerHTML = `<div class="tab ${currentCategory === 'Barchasi' ? 'active' : ''}" onclick="filterCategory('Barchasi')">Barchasi</div>`;
    
    let categories = window.allCategories || [...new Set(products.map(p => p.category))];
    categories.forEach(cat => {
        let activeClass = currentCategory === cat ? 'active' : '';
        tabsContainer.innerHTML += `<div class="tab ${activeClass}" onclick="filterCategory('${cat}')">${cat}</div>`;
    });
}

function filterCategory(category) {
    currentCategory = category;
    tg.HapticFeedback.selectionChanged();
    renderTabs();
    renderProducts();
}

function renderProducts() {
    const container = document.getElementById("products");
    container.innerHTML = "";
    
    let filtered = currentCategory === 'Barchasi' ? products : products.filter(p => p.category === currentCategory);
    
    filtered.forEach(p => {
        let qty = cart[p.id] || 0;
        let card = document.createElement('div');
        card.className = "card";
        
        let actionsHtml = qty === 0 
            ? `<button class="btn" onclick="add(${p.id})"><i class="fa-solid fa-bag-shopping"></i> Qo'shish</button>`
            : `<div class="controls">
                 <button class="btn-icon" onclick="remove(${p.id})">-</button>
                 <span class="qty">${qty}</span>
                 <button class="btn-icon" onclick="add(${p.id})">+</button>
               </div>`;
               
        card.innerHTML = `
            <i class="fa-regular fa-heart card-heart"></i>
            <div class="card-img-container">
                <img src="${p.image}" alt="${p.name}">
            </div>
            <div class="card-info">
                <h3>${p.name}</h3>
                <p>${p.desc}</p>
                <span class="price">${formatPrice(p.price)} so'm</span>
            </div>
            <div class="actions" id="actions-${p.id}">${actionsHtml}</div>
        `;
        container.appendChild(card);
    });
    
    updateMainButton();
}

function getActionsHtml(id, qty) {
    let p = products.find(x => x.id == id);
    if(qty === 0) {
        return `<button class="btn" onclick="add(${p.id})"><i class="fa-solid fa-bag-shopping"></i> Qo'shish</button>`;
    } else {
        return `<div class="controls">
                 <button class="btn-icon" onclick="remove(${p.id})">-</button>
                 <span class="qty">${qty}</span>
                 <button class="btn-icon" onclick="add(${p.id})">+</button>
               </div>`;
    }
}

function updateProductUI(id) {
    let qty = cart[id] || 0;
    let actionsContainer = document.getElementById(`actions-${id}`);
    if(actionsContainer) {
        actionsContainer.innerHTML = getActionsHtml(id, qty);
    }
    updateMainButton();
}

function add(id) {
    if(!cart[id]) cart[id] = 0;
    cart[id]++;
    tg.HapticFeedback.impactOccurred('light');
    updateProductUI(id);
}

function remove(id) {
    if(cart[id]) {
        cart[id]--;
        if(cart[id] === 0) delete cart[id];
        tg.HapticFeedback.impactOccurred('light');
    }
    updateProductUI(id);
}

function updateMainButton() {
    let total = 0;
    let count = 0;
    for(let id in cart) {
        let p = products.find(x => x.id == id);
        total += p.price * cart[id];
        count += cart[id];
    }
    
    if(count > 0) {
        tg.MainButton.text = `Savatga o'tish (${formatPrice(total)} so'm)`;
        tg.MainButton.color = '#5F7149';
        tg.MainButton.show();
    } else {
        tg.MainButton.hide();
    }
}

tg.MainButton.onClick(() => {
    let orderItems = [];
    for(let id in cart) {
        let p = products.find(x => x.id == id);
        orderItems.push({ id: p.id, name: p.name, price: p.price, quantity: cart[id] });
    }
    tg.sendData(JSON.stringify({ action: "checkout", items: orderItems }));
});

loadProducts();
