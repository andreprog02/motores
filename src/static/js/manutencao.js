/* src/static/js/bloqueio_pecas.js */
document.addEventListener("DOMContentLoaded", function() {
    const $ = django.jQuery;

    const selectAtividade = $('#id_tipo_atividade');
    
    // Identifica os campos que queremos bloquear
    // O Django Select2 (Autocomplete) usa um <select> escondido, precisamos bloquear ele E o container visual
    const campoPeca = $('#id_item_estoque_utilizado');
    const campoSerial = $('#id_novo_serial_number');

    function gerenciarBloqueio() {
        const valor = selectAtividade.val();
        
        // Verifique se no banco é 'TROCA', 'SUBSTITUICAO' ou 'CORRETIVA'
        // Ajuste conforme seus Choices do models.py
        const permitePeca = (valor === 'TROCA' || valor === 'SUBSTITUICAO');

        if (permitePeca) {
            // DESTRAVA
            campoPeca.prop('disabled', false);
            campoSerial.prop('disabled', false);
            campoSerial.prop('readonly', false);
            
            // Remove estilo visual de desabilitado (opacidade)
            campoPeca.closest('.form-row').css('opacity', '1');
            campoSerial.closest('.form-row').css('opacity', '1');

        } else {
            // TRAVA
            campoPeca.val(null).trigger('change'); // Limpa o valor selecionado para evitar erro
            campoPeca.prop('disabled', true);
            
            campoSerial.val(''); // Limpa o serial
            campoSerial.prop('readonly', true); // Readonly é melhor que disabled para texto para permitir copiar
            
            // Adiciona estilo visual de desabilitado (cinza)
            campoPeca.closest('.form-row').css('opacity', '0.5');
            campoSerial.closest('.form-row').css('opacity', '0.5');
        }
    }

    // Roda ao iniciar
    gerenciarBloqueio();

    // Roda ao mudar
    selectAtividade.change(gerenciarBloqueio);
});