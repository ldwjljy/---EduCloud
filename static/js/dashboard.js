document.addEventListener('DOMContentLoaded',()=>{
  const gradePieEl=document.getElementById('gradePie');
  if(gradePieEl){
    new Chart(gradePieEl,{type:'doughnut',data:{labels:['大一','大二','大三','大四'],datasets:[{data:[26,25,24,25],backgroundColor:['#f39c12','#27ae60','#3498db','#f1c40f']}]}});
  }
  const trendLineEl=document.getElementById('trendLine');
  if(trendLineEl){
    new Chart(trendLineEl,{type:'line',data:{labels:['2019','2020','2021','2022','2023'],datasets:[{label:'学生人数',data:[9500,10200,11000,12000,13000],borderColor:'#e74c3c'},{label:'教职工人数',data:[500,520,540,560,580],borderColor:'#2ecc71'}]}});
  }
  const positionPieEl=document.getElementById('positionPie');
  if(positionPieEl){
    new Chart(positionPieEl,{type:'pie',data:{labels:['院长','副院长','班主任','教师'],datasets:[{data:[5,15,30,50],backgroundColor:['#e67e22','#16a085','#2c3e50','#f97316']}]}});
  }
  const hotBarEl=document.getElementById('hotBar');
  if(hotBarEl){
    new Chart(hotBarEl,{type:'bar',data:{labels:['软件工程实践','计算机网络','人工智能导论','高等数学','数据结构算法'],datasets:[{label:'选课人数',data:[1200,1000,1100,900,1300],backgroundColor:'#e67e22'}]},options:{indexAxis:'y'}});
  }
});
