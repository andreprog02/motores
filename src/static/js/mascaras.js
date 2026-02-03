/* src/static/js/mascaras.js */
(function($) {
    $(document).ready(function() {
        // Lista de IDs dos campos que queremos formatar como INTEIROS com separador de milhar
        var camposParaMascarar = [
            // App Assets (Motor)
            '#id_horas_totais',
            '#id_total_arranques',
            '#id_hora_motor_instalacao',
            '#id_arranques_motor_instalacao',
            
            // App Inventory (Estoque)
            '#id_quantidade',
            '#id_minimo_seguranca',
            '#id_vida_util_horas',
            '#id_vida_util_arranques',
            
            // App Maintenance (Manutenção)
            '#id_horimetro_na_execucao'
        ];

        function aplicarMascaraInteiro() {
            var $input = $(this);
            var valor = $input.val();

            // 1. Limpeza: Remove tudo que NÃO for número (incluindo pontos antigos e vírgulas)
            // Isso garante que estamos trabalhando "só com números inteiros" como você pediu
            valor = valor.replace(/\D/g, "");

            // 2. Formatação: Adiciona o ponto a cada 3 dígitos
            // Regex mágica: olha para frente e vê se tem múltiplos de 3 dígitos sobrando
            valor = valor.replace(/(\d)(?=(\d{3})+(?!\d))/g, "$1.");

            // 3. Aplica de volta no campo
            $input.val(valor);
        }

        camposParaMascarar.forEach(function(seletor) {
            var $campo = $(seletor);
            
            if ($campo.length > 0) {
                // Truque: Mudamos o type para 'text' para o navegador aceitar o ponto
                // (Inputs do type='number' geralmente rejeitam formatação visual)
                $campo.attr('type', 'text');
                
                // Aplica a cada tecla digitada
                $campo.on('input', aplicarMascaraInteiro);
                
                // Aplica ao carregar a página (para editar registros existentes)
                aplicarMascaraInteiro.call($campo);
            }
        });
    });
})(django.jQuery);