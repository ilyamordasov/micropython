// pulse timer native module
// Copyright © 2020 by Thorsten von Eicken.

#include <assert.h>
#include <string.h>
#include <stdio.h>
#include <math.h>
#include "py/dynruntime.h"
// ESP-IDF imports
#include <esp_err.h>
#include <driver/pcnt.h>
#include "esp_attr.h"
#include "esp_log.h"

#define PCNT_H_LIM_VAL      256
#define PCNT_L_LIM_VAL     -10
#define PCNT_THRESH1_VAL    5
#define PCNT_THRESH0_VAL   -5
#define PCNT_INPUT_SIG_IO   18  // Pulse Input GPIO
#define PCNT_INPUT_CTRL_IO  5  // Control GPIO HIGH=count up, LOW=count down

typedef struct {
    int unit;  // the PCNT unit that originated an interrupt
    uint32_t status; // information on the event type that caused the interrupt
} pcnt_evt_t;

pcnt_evt_t evt;

// from smallint.h
#define MP_SMALL_INT_POSITIVE_MASK ~(WORD_MSBIT_HIGH | (WORD_MSBIT_HIGH >> 1))

extern bool mp_sched_schedule(mp_obj_t function, mp_obj_t arg);
extern void mp_hal_wake_main_task_from_isr(void);

uint8_t id;
uint8_t length;

mp_int_t p_period = 0;
mp_int_t p_width = 0;
mp_int_t p_high = 0;
mp_int_t p_low = 0;

mp_int_t _cnt = 0;
mp_int_t code = 0;

mp_obj_t l;

static void IRAM_ATTR pcnt_example_intr_handler(void *arg)
{
    uint32_t intr_status = PCNT.int_st.val;
    int i;
    pcnt_evt_t evt;

    for (i = 0; i < PCNT_UNIT_MAX; i++) {
        if (intr_status & (BIT(i))) {
            evt.unit = i;
            /* Save the PCNT event type that caused an interrupt
               to pass it to the main program */
            evt.status = PCNT.status_unit[i].val;
            PCNT.int_clr.val = BIT(i);
            mp_printf(&mp_plat_print, "[MAIXPY]: Can not create decode object\n");
        }
    }
}

static void pcnt_example_init(int unit)
{
    /* Prepare configuration for the PCNT unit */
    pcnt_config_t pcnt_config = {
        // Set PCNT input signal and control GPIOs
        .pulse_gpio_num = PCNT_INPUT_SIG_IO,
        .ctrl_gpio_num = PCNT_INPUT_CTRL_IO,
        .channel = PCNT_CHANNEL_0,
        .unit = unit,
        // What to do on the positive / negative edge of pulse input?
        .pos_mode = PCNT_COUNT_INC,   // Count up on the positive edge
        .neg_mode = PCNT_COUNT_DIS,   // Keep the counter value on the negative edge
        // What to do when control input is low or high?
        .lctrl_mode = PCNT_MODE_REVERSE, // Reverse counting direction if low
        .hctrl_mode = PCNT_MODE_KEEP,    // Keep the primary counter mode if high
        // Set the maximum and minimum limit values to watch
        .counter_h_lim = PCNT_H_LIM_VAL,
        .counter_l_lim = PCNT_L_LIM_VAL,
    };
    /* Initialize PCNT unit */
    pcnt_unit_config(&pcnt_config);

    /* Configure and enable the input filter */
    pcnt_set_filter_value(unit, 100);
    pcnt_filter_enable(unit);

    /* Set threshold 0 and 1 values and enable events to watch */
    pcnt_set_event_value(unit, PCNT_EVT_THRES_1, PCNT_THRESH1_VAL);
    pcnt_event_enable(unit, PCNT_EVT_THRES_1);
    pcnt_set_event_value(unit, PCNT_EVT_THRES_0, PCNT_THRESH0_VAL);
    pcnt_event_enable(unit, PCNT_EVT_THRES_0);
    /* Enable events on zero, maximum and minimum limit values */
    pcnt_event_enable(unit, PCNT_EVT_ZERO);
    pcnt_event_enable(unit, PCNT_EVT_H_LIM);
    pcnt_event_enable(unit, PCNT_EVT_L_LIM);

    /* Initialize PCNT's counter */
    pcnt_counter_pause(unit);
    pcnt_counter_clear(unit);

    /* Install interrupt service and add isr callback handler */
    pcnt_isr_service_install(0);
    pcnt_isr_handler_add(unit, pcnt_example_intr_handler, (void *)unit);

    /* Everything is set up, now go to counting */
    pcnt_counter_resume(unit);
}

// uint32_t mp_hal_ticks_us(void) {
//     return esp_timer_get_time();
// }

// uint32_t time_diff(mp_obj_t end_in, mp_obj_t start_in) {
//     // we assume that the arguments come from ticks_xx so are small ints
//     mp_uint_t start = MP_OBJ_SMALL_INT_VALUE(start_in);
//     mp_uint_t end = MP_OBJ_SMALL_INT_VALUE(end_in);
//     // Optimized formula avoiding if conditions. We adjust difference "forward",
//     // wrap it around and adjust back.
//     mp_int_t diff = ((end - start + MICROPY_PY_UTIME_TICKS_PERIOD / 2) & (MICROPY_PY_UTIME_TICKS_PERIOD - 1)) - MICROPY_PY_UTIME_TICKS_PERIOD / 2;
//     return diff;
// }

// STATIC void GDO_isr_handler(void *arg) {
    
//     uint8_t value = gpio_get_level(id);
//     mp_int_t tick = esp_timer_get_time() & (MICROPY_PY_UTIME_TICKS_PERIOD - 1);
//     mp_obj_t handler = arg;
    
//     if (value == 1){
//         if (p_high != 0){

//             p_period = time_diff(MP_OBJ_NEW_SMALL_INT(tick), MP_OBJ_NEW_SMALL_INT(p_high));
//             p_high = tick;
//             mp_obj_tuple_t *t = mp_obj_new_tuple(3, NULL);
//             t->items[0] = MP_OBJ_NEW_SMALL_INT(p_width);
//             t->items[1] = MP_OBJ_NEW_SMALL_INT(time_diff(MP_OBJ_NEW_SMALL_INT(p_period), MP_OBJ_NEW_SMALL_INT(p_width)));
//             t->items[2] = MP_OBJ_NEW_SMALL_INT(p_period);
//             //mp_obj_list_append(l, t);
//             _cnt ++;
//             //if (_cnt > 100)
//             //{
//                 mp_sched_schedule(handler, MP_OBJ_FROM_PTR(t));
//                 mp_hal_wake_main_task_from_isr();
//             //}
//             /*if (p_width < p_period) {
//                 uint8_t bit = (p_width < (p_period + (p_period % 10)) / 2) ? 1 : 0;
//                 code = (code << 1) | bit;
//                 _cnt++;
//                 mp_obj_tuple_t *t = mp_obj_new_tuple(5, NULL);
//                 t->items[0] = MP_OBJ_NEW_SMALL_INT(p_width);
//                 t->items[1] = MP_OBJ_NEW_SMALL_INT(p_period);
//                 t->items[2] = MP_OBJ_NEW_SMALL_INT(bit);
//                 t->items[3] = MP_OBJ_NEW_SMALL_INT(code);
//                 t->items[4] = MP_OBJ_NEW_SMALL_INT(_cnt);
//                 mp_obj_list_append(l, t);
//             }

//             if (p_period > 3500) {
//                 p_period = p_width = p_high = code = 0;
//             }
//             if (_cnt >= 77)
//             {
//                 mp_sched_schedule(handler, MP_OBJ_FROM_PTR(l));
//                 mp_hal_wake_main_task_from_isr();
//             }*/
//         }
//         else {
//             p_high = tick;
//         }
//     }
//     else if (value == 0) {
//         p_width = time_diff(MP_OBJ_NEW_SMALL_INT(tick), MP_OBJ_NEW_SMALL_INT(p_high));
//     }
    
//     //uint32_t tick = esp_timer_get_time() & (MICROPY_PY_UTIME_TICKS_PERIOD - 1);
//     /*if (value == 1) {
//         high_start = esp_timer_get_time() & (MICROPY_PY_UTIME_TICKS_PERIOD - 1);
//         low_us = abs((esp_timer_get_time() & (MICROPY_PY_UTIME_TICKS_PERIOD - 1)) - low_start);
//     }
//     else if (value == 0) {
//         low_start = esp_timer_get_time() & (MICROPY_PY_UTIME_TICKS_PERIOD - 1);
//         high_us = abs((esp_timer_get_time() & (MICROPY_PY_UTIME_TICKS_PERIOD - 1)) - high_start);
//         bit = (high_us > low_us) ? 1 : 0;
//         period_width = high_us + low_us;
//         period_diff = abs(last_period - period_width);
//         grace = period_width / 10;
//         if (period_diff > grace) {
//             // start new code
//             _cnt = 0;
//             code = bit;
//         }
//         else {
//             _cnt += 1;
//             code <<= 1;
//             code |= bit;
//         }
//         if (_cnt >= length-1) {
//             high_start = low_start = high_us = low_us = period_width = period_diff = grace = last_period = bit = _cnt = code = 0;
//             mp_obj_t handler = arg;
//             mp_sched_schedule(handler, MP_OBJ_NEW_SMALL_INT(code));
//             mp_hal_wake_main_task_from_isr();
//         }
//         else
//             last_period = period_width;
//     }*/
// }

STATIC mp_obj_t readGDO(mp_obj_t pin, mp_obj_t handler, mp_obj_t len) {
        /*id = (uint)mp_obj_get_int(pin);
        length = (uint)mp_obj_get_int(len);

        l = mp_obj_new_list(0, 0);

        esp_err_t err = gpio_isr_handler_add(id, GDO_isr_handler, (void *)handler);
        const char* ret = esp_err_to_name(err);
        _cnt = p_period = p_width = p_high = code = 0;
        return ret ? mp_obj_new_str(ret, strlen(ret)) : mp_const_none; */
        int pcnt_unit = PCNT_UNIT_0;
        pcnt_example_init(pcnt_unit);
        return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_3(readGDO_obj, readGDO);


mp_obj_t mpy_init(mp_obj_fun_bc_t *self, size_t n_args, size_t n_kw, mp_obj_t *args) {
        MP_DYNRUNTIME_INIT_ENTRY
        mp_store_global(MP_QSTR_readGDO, MP_OBJ_FROM_PTR(&readGDO_obj));
        MP_DYNRUNTIME_INIT_EXIT
}
