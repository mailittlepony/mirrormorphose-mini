/*
 * Copyright (C) 2025 Stanley Arnaud <stantonik@stantonik-mba.local>
 *
 * Distributed under terms of the MIT license.
 */

/**
 * @file overlayx.c
 * @brief
 *
 * @author Stanley Arnaud
 * @date 06/27/2025
 * @version 0
 */

// -----------------------------------------------------------------------------
// Includes
// -----------------------------------------------------------------------------
#include "overlayx.h"

#define STB_IMAGE_IMPLEMENTATION
#include "./lib/stb/stb_image.h"

#include <bcm_host.h>
#include <stdio.h>
#include <unistd.h>

// -----------------------------------------------------------------------------
// Macros and Constants
// -----------------------------------------------------------------------------
#define IMAGE_FORMAT VC_IMAGE_RGBA16

#define FADE_LAYER 3
#define VIGNETTE_LAYER 2

// -----------------------------------------------------------------------------
// Static Variables
// -----------------------------------------------------------------------------
static DISPMANX_DISPLAY_HANDLE_T display;

static DISPMANX_RESOURCE_HANDLE_T vignette_res;
static DISPMANX_ELEMENT_HANDLE_T vignette_elmt;
static DISPMANX_RESOURCE_HANDLE_T fade_res;
static DISPMANX_ELEMENT_HANDLE_T fade_elmt;

static uint32_t screen_width, screen_height;
static int display_num = 0;

// -----------------------------------------------------------------------------
// Static Function Declarations
// -----------------------------------------------------------------------------

// -----------------------------------------------------------------------------
// Static Function Definitions
// -----------------------------------------------------------------------------

// -----------------------------------------------------------------------------
// Function Definitions
// -----------------------------------------------------------------------------
int overlay_init(const char *img_path)
{
    bcm_host_init();

    // Create display and get size
    display = vc_dispmanx_display_open(display_num);
    if (!display)
    {
        fprintf(stderr, "Failed to open display\n");
        return 1;
    }

    if (graphics_get_display_size(display_num, &screen_width, &screen_height) <
        0)
    {
        fprintf(stderr, "Failed to get display size\n");
        return 1;
    }

    VC_RECT_T src_rect;
    vc_dispmanx_rect_set(&src_rect, 0, 0, screen_width << 16,
                         screen_height << 16);
    VC_RECT_T dst_rect;
    vc_dispmanx_rect_set(&dst_rect, 0, 0, screen_width, screen_height);

    // Resources allocation
    uint32_t vc_image_ptr;
    fade_res = vc_dispmanx_resource_create(IMAGE_FORMAT, screen_width,
                                           screen_height, &vc_image_ptr);
    if (fade_res)
    {
        fprintf(stderr, "Failed to create resource\n");
        return 1;
    }

    // Create fade overlay
    int pitch = (screen_width * 2 + 31) & ~31;
    uint16_t *fade_img = malloc(pitch * screen_height);
    if (fade_img == NULL)
    {
        fprintf(stderr, "Memory allocation failed for fade image\n");
        return 1;
    }

    for (int i = 0; i < screen_width * screen_height; i++)
    {
        fade_img[i] = 0x000F;
    }

    vc_dispmanx_resource_write_data(fade_res, IMAGE_FORMAT, pitch, fade_img,
                                    &dst_rect);
    free(fade_img);

    // Create vignette overlay
    if (strlen(img_path) > 0)
    {
        vignette_res = vc_dispmanx_resource_create(
            IMAGE_FORMAT, screen_width, screen_height, &vc_image_ptr);

        if (vignette_res)
        {
            fprintf(stderr, "Failed to create resource\n");
            return 1;
        }

        int width, height, chans;
        uint16_t *vignette_img = malloc(pitch * screen_height);
        uint8_t *data = stbi_load(img_path, &width, &height, &chans, 0);
        if (vignette_img == NULL | data == NULL)
        {
            fprintf(stderr, "Memory allocation failed for vignette image\n");
            return 1;
        }

        if (width != screen_width || height != screen_height)
        {
            fprintf(stderr,
                    "Vignette image size is not the same as the screen size");
            return 1;
        }

        for (int y = 0; y < screen_height; y++)
        {
            for (int x = 0; x < screen_width; x++)
            {
                int src_i = (y * width + x) * 4;
                int dst_i = y * (pitch / 2) + x;

                uint8_t r = data[src_i + 0] >> 4;
                uint8_t g = data[src_i + 1] >> 4;
                uint8_t b = data[src_i + 2] >> 4;
                uint8_t a = data[src_i + 3] >> 4;

                // Pack into R4G4B4A4 format: RRRRGGGGBBBBAAAA
                vignette_img[dst_i] = (r << 12) | (g << 8) | (b << 4) | a;
            }
        }
        free(data);
        vc_dispmanx_resource_write_data(vignette_res, IMAGE_FORMAT, pitch,
                                        vignette_img, &dst_rect);
        free(vignette_img);
    }

    VC_DISPMANX_ALPHA_T fade_alpha = {
        .flags = DISPMANX_FLAGS_ALPHA_FIXED_ALL_PIXELS,
        .opacity = 255,
        .mask = 0,
    };

    DISPMANX_UPDATE_HANDLE_T update = vc_dispmanx_update_start(display_num);

    if (strlen(img_path) > 0)
    {
        vignette_elmt = vc_dispmanx_element_add(
            update, display, VIGNETTE_LAYER, &dst_rect, vignette_res, &src_rect,
            DISPMANX_PROTECTION_NONE, NULL, NULL, VC_IMAGE_ROT0);
    }

    fade_elmt = vc_dispmanx_element_add(
        update, display, FADE_LAYER, &dst_rect, fade_res, &src_rect,
        DISPMANX_PROTECTION_NONE, &fade_alpha, NULL, VC_IMAGE_ROT0);

    vc_dispmanx_update_submit_sync(update);

    return 0;
}

int overlay_start_fade_in(int duration_ms, int step)
{
    int delay_us = (duration_ms * 1000) / ((255 + step - 1) / step);

    for (int a = 255; a >= 0; a -= step)
    {
        DISPMANX_UPDATE_HANDLE_T update = vc_dispmanx_update_start(display_num);
        vc_dispmanx_element_change_attributes(update, fade_elmt, 2, FADE_LAYER,
                                              (uint8_t)a, NULL, NULL, 0, 0);
        vc_dispmanx_update_submit_sync(update);
        usleep(delay_us);
    }

    return 0;
}

int overlay_start_fade_out(int duration_ms, int step)
{
    int delay_us = (duration_ms * 1000) / ((255 + step - 1) / step);

    for (int a = 0; a < 256; a += step)
    {
        DISPMANX_UPDATE_HANDLE_T update = vc_dispmanx_update_start(display_num);
        vc_dispmanx_element_change_attributes(update, fade_elmt, 2, FADE_LAYER,
                                              (uint8_t)a, NULL, NULL, 0, 0);
        vc_dispmanx_update_submit_sync(update);
        usleep(delay_us);
    }

    return 0;
}

int overlay_free(void)
{
    DISPMANX_UPDATE_HANDLE_T update = vc_dispmanx_update_start(0);
    vc_dispmanx_element_remove(update, vignette_elmt);
    vc_dispmanx_element_remove(update, fade_elmt);
    vc_dispmanx_update_submit_sync(update);

    vc_dispmanx_resource_delete(vignette_res);
    vc_dispmanx_resource_delete(fade_res);
    vc_dispmanx_display_close(display);

    return 0;
}
