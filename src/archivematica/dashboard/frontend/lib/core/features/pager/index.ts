const buildPageUrl = (searchParams: string, pageValue: string): string => {
  const normalizedSearchParams = searchParams.trim()
  if (!normalizedSearchParams) {
    return `?page=${encodeURIComponent(pageValue)}`
  }

  return `?${normalizedSearchParams}&page=${encodeURIComponent(pageValue)}`
}

const initPager = (): void => {
  const jumpInputs = document.querySelectorAll<HTMLInputElement>('.js-paging-jump')

  jumpInputs.forEach((input) => {
    input.addEventListener('change', () => {
      const pageValue = input.value.trim()
      if (!pageValue) {
        return
      }

      const searchParams = input.dataset.searchParams ?? ''
      const nextUrl = buildPageUrl(searchParams, pageValue)
      window.location.assign(nextUrl)
    })
  })
}

export function init(): void {
  initPager()
}
