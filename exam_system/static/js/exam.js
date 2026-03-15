document.addEventListener("DOMContentLoaded", function(){

/* ================= DATA FROM TEMPLATE ================= */

const examData = document.getElementById("exam-data");

if(!examData){
    console.error("Exam data element not found");
    return;
}

const remainingTime = Number(examData.dataset.remaining);
const totalQuestions = Number(examData.dataset.total);
const examId = examData.dataset.exam;

/* ================= TIMER ================= */

const timerDisplay = document.getElementById("timer");
const form = document.querySelector("form");

let endTime = Date.now() + (remainingTime * 1000);

function updateTimer(){

    const now = Date.now();
    const timeLeft = Math.floor((endTime - now) / 1000);

    if(timeLeft <= 0){
        form.submit();
        return;
    }

    const minutes = Math.floor(timeLeft / 60);
    const seconds = timeLeft % 60;

    timerDisplay.textContent =
        minutes + ":" + (seconds < 10 ? "0" : "") + seconds;

}

updateTimer();
setInterval(updateTimer,1000);

/* ================= DOM ELEMENTS ================= */

const radios = document.querySelectorAll('input[type="radio"]');
const progressBar = document.getElementById("progressBar");
const flagButtons = document.querySelectorAll(".flag-btn");
const submitBtn = document.querySelector('button[type="submit"]');

const questionCards = document.querySelectorAll(".question-card");
const nextButtons = document.querySelectorAll(".next-btn");
const prevButtons = document.querySelectorAll(".prev-btn");

const answeredCount = document.getElementById("answeredCount");
const unansweredCount = document.getElementById("unansweredCount");
const flaggedCount = document.getElementById("flaggedCount");

/* ================= PROGRESS BAR ================= */

function updateProgress(){

    const answered = document.querySelectorAll('input[type="radio"]:checked').length;
    const percent = Math.round((answered / totalQuestions) * 100);

    progressBar.style.width = percent + "%";
    progressBar.innerText = percent + "%";
}

radios.forEach(radio=>{
    radio.addEventListener("change",updateProgress);
});

/* ================= NAVIGATOR + FLAG ================= */

flagButtons.forEach(btn=>{

    btn.addEventListener("click",function(){

        const q = this.dataset.question;
        const nav = document.getElementById("nav"+q);

        nav.classList.remove("btn-outline-secondary","btn-success");
        nav.classList.add("btn-warning");

        updateCounts();
    });

});

radios.forEach(radio=>{

    radio.addEventListener("change",function(){

        const questionDiv = this.closest(".card").id;
        const qNumber = questionDiv.replace("question","");

        const nav = document.getElementById("nav"+qNumber);

        nav.classList.remove("btn-outline-secondary","btn-warning");
        nav.classList.add("btn-success");

        updateCounts();
    });

});

/* ================= QUESTION COUNTERS ================= */

function updateCounts(){

    const answered = document.querySelectorAll('input[type="radio"]:checked').length;
    const flagged = document.querySelectorAll('.nav-btn.btn-warning').length;

    answeredCount.textContent = answered;
    unansweredCount.textContent = totalQuestions - answered;
    flaggedCount.textContent = flagged;
}

/* ================= AUTO SAVE ================= */

const examKey = "exam_" + examId;

window.addEventListener("load",function(){

    const savedAnswers = JSON.parse(localStorage.getItem(examKey)) || {};

    radios.forEach(function(radio){

        if(savedAnswers[radio.name] == radio.value){
            radio.checked = true;
        }

    });

    updateCounts();
    updateProgress();
});

radios.forEach(function(radio){

    radio.addEventListener("change",function(){

        const savedAnswers = JSON.parse(localStorage.getItem(examKey)) || {};
        savedAnswers[this.name] = this.value;

        localStorage.setItem(examKey,JSON.stringify(savedAnswers));
    });

});

/* ================= FINAL REVIEW ================= */

submitBtn.addEventListener("click",function(e){

    const answered = document.querySelectorAll('input[type="radio"]:checked').length;
    const unanswered = totalQuestions - answered;

    let message = `You answered ${answered} out of ${totalQuestions} questions.\n`;
    message += `Unanswered: ${unanswered}\n\n`;
    message += "Are you sure you want to submit the exam?";

    if(!confirm(message)){
        e.preventDefault();
        return;
    }

    localStorage.removeItem(examKey);
    localStorage.removeItem(examKeyTimer);
});

/* ================= TAB SWITCH DETECTION ================= */

let tabSwitchCount = 0;

document.addEventListener("visibilitychange",function(){

    if(document.hidden){

        tabSwitchCount++;

        if(tabSwitchCount === 1){
            alert("Warning: Tab switching detected (1/3).");
        }

        else if(tabSwitchCount === 2){
            alert("Warning: Tab switching detected (2/3). One more and the exam will auto submit.");
        }

        else if(tabSwitchCount >= 3){
            alert("Too many tab switches. Exam will be submitted.");
            form.submit();
        }

    }

});

/* ================= ACTIVE QUESTION HIGHLIGHT ================= */

function highlightQuestion(index){

    questionCards.forEach(q => q.classList.remove("active-question"));
    questionCards[index].classList.add("active-question");

}

/* ================= PAGINATION ================= */

let currentQuestion = 0;

function showQuestion(index){

    questionCards.forEach(q => q.style.display = "none");

    questionCards[index].style.display = "block";

    highlightQuestion(index);
}

showQuestion(currentQuestion);

nextButtons.forEach(btn => {

    btn.addEventListener("click",function(){

        if(currentQuestion < questionCards.length - 1){
            currentQuestion++;
            showQuestion(currentQuestion);
        }

    });

});

prevButtons.forEach(btn => {

    btn.addEventListener("click",function(){

        if(currentQuestion > 0){
            currentQuestion--;
            showQuestion(currentQuestion);
        }

    });

});

});