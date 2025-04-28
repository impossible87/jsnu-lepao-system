document.addEventListener('DOMContentLoaded', function() {
    const timeForms = document.getElementById('time-forms');
    const addTimeBtn = document.getElementById('add-time');
    const generateBtn = document.getElementById('generate');
    let formCount = 1;

    // 验证时间输入
    function validateTimeInput(input) {
        const value = parseInt(input.value);
        const min = parseInt(input.min);
        const max = parseInt(input.max);
        
        if (isNaN(value) || value < min || value > max) {
            input.classList.add('is-invalid');
            return false;
        }
        input.classList.remove('is-invalid');
        return true;
    }

    // 验证整个表单
    function validateForm(form) {
        let isValid = true;
        const inputs = form.querySelectorAll('input');
        
        inputs.forEach(input => {
            if (!validateTimeInput(input)) {
                isValid = false;
            }
        });

        // 验证月份和日期
        const year = parseInt(form.querySelector('.year').value);
        const month = parseInt(form.querySelector('.month').value);
        const day = parseInt(form.querySelector('.day').value);
        
        if (isValid) {
            const lastDay = new Date(year, month, 0).getDate();
            if (day > lastDay) {
                form.querySelector('.day').classList.add('is-invalid');
                isValid = false;
            }
        }

        return isValid;
    }

    // 添加新的时间表单
    addTimeBtn.addEventListener('click', function() {
        formCount++;
        const newForm = document.querySelector('.time-form').cloneNode(true);
        newForm.querySelector('h3').textContent = `跑步时间 #${formCount}`;
        newForm.querySelector('.remove-time').style.display = 'block';
        
        // 清空输入值
        const inputs = newForm.querySelectorAll('input');
        inputs.forEach(input => {
            input.value = '';
            input.classList.remove('is-invalid');
        });
        
        timeForms.appendChild(newForm);
    });

    // 删除时间表单
    timeForms.addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-time')) {
            if (formCount > 1) {
                e.target.closest('.time-form').remove();
                formCount--;
                
                // 更新剩余表单的标题
                const forms = document.querySelectorAll('.time-form');
                forms.forEach((form, index) => {
                    form.querySelector('h3').textContent = `跑步时间 #${index + 1}`;
                });
            }
        }
    });

    // 输入验证
    timeForms.addEventListener('input', function(e) {
        if (e.target.classList.contains('form-control')) {
            validateTimeInput(e.target);
        }
    });

    // 生成TCX文件
    generateBtn.addEventListener('click', function() {
        const forms = document.querySelectorAll('.time-form');
        const times = [];
        let isValid = true;

        forms.forEach(form => {
            if (!validateForm(form)) {
                isValid = false;
                return;
            }

            const year = form.querySelector('.year').value;
            const month = form.querySelector('.month').value;
            const day = form.querySelector('.day').value;
            const hour = form.querySelector('.hour').value;
            const minute = form.querySelector('.minute').value;
            const second = form.querySelector('.second').value;

            times.push({
                year: parseInt(year),
                month: parseInt(month),
                day: parseInt(day),
                hour: parseInt(hour),
                minute: parseInt(minute),
                second: parseInt(second)
            });
        });

        if (!isValid) {
            alert('请检查输入的时间是否有效');
            return;
        }

        // 发送请求生成文件
        fetch('/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ times: times })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('生成文件失败');
            }
            return response.blob();
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = times.length > 1 ? 'runs.zip' : `run_${times[0].year}${times[0].month}${times[0].day}_${times[0].hour}${times[0].minute}${times[0].second}.tcx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
        })
        .catch(error => {
            alert('生成文件时出错：' + error.message);
        });
    });

    // 设置当前时间为默认值
    const now = new Date();
    const firstForm = document.querySelector('.time-form');
    firstForm.querySelector('.year').value = now.getFullYear();
    firstForm.querySelector('.month').value = now.getMonth() + 1;
    firstForm.querySelector('.day').value = now.getDate();
    firstForm.querySelector('.hour').value = now.getHours();
    firstForm.querySelector('.minute').value = now.getMinutes();
    firstForm.querySelector('.second').value = now.getSeconds();
}); 
