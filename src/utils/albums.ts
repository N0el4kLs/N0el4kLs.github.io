// 定义 ImageMetadata 类型，如果在其他地方已定义可以省略
type ImageMetadata = {
  src: string;
  width: number;
  height: number;
  format: string;
};

export async function getAlbumImages(albumId: string) {
  // 1. 列出所有相册文件
  let images = import.meta.glob<{ default: ImageMetadata }>(
    "/src/content/albums/**/*.{jpeg,jpg,png,webp}"
  );

  // 2. 根据相册ID过滤图片
  images = Object.fromEntries(
    Object.entries(images).filter(([key]) => key.includes(albumId))
  );

  // 3. 解析图片导入
  const resolvedImages = await Promise.all(
    Object.values(images).map((image) => image().then((mod) => mod.default))
  );

  // 4. 随机排序图片（可选）
  resolvedImages.sort(() => Math.random() - 0.5);
  return resolvedImages;
}