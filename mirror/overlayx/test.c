
#include "overlayx.h"


int main(void)
{
	overlay_init();
	overlay_start_fade_in(1000, 5);
	overlay_start_fade_out(1000, 5);
	overlay_free();
	return 0;
}
